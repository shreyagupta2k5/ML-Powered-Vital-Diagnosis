"""
Ensemble API Gateway — Main entry point for unified risk prediction.
Routes requests to individual tracks, aggregates results, returns Phase 7 compliant output.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal, Any
import httpx
import asyncio
import json
import pathlib
from datetime import datetime, timezone
from ..services.aggregator import EnsembleAggregator
from ..services.risk_scorer import RiskScorer
import os
from backend_main.websockets.alert_stream import publish_high_risk
from backend_shared.db.logger import log_prediction
import uuid  # Added for generating request IDs

# ── Registry & Drift imports (Tasks 3.2 & 3.3) ───────────────────────────────
from backend_shared.registry.model_registry import (
    list_versions, get_active_version, register_model, promote_to_active
)
from backend_shared.registry.model_loader import hot_swap, list_loaded
from backend_shared.mlops.retrain_trigger import run_drift_cycle
from backend_shared.mlops.drift_monitor import check_drift_for_track

router = APIRouter(prefix="/api/v1/ensemble", tags=["Ensemble Layer"])
registry_router = APIRouter(prefix="/api/v1/registry", tags=["Model Registry"])
drift_router = APIRouter(prefix="/api/v1/drift", tags=["Drift Monitor"])

# Configuration
CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "weights.json"

# ── Track URLs (Aligned with backend folder structure) ────────────────────────
TRACK1_EICU_URL = f"{os.getenv('TRACK1_URL', 'http://127.0.0.1:8000')}/api/v1/track1/predict"
TRACK2_MIMIC_URL = f"{os.getenv('TRACK2_URL', 'http://127.0.0.1:8000')}/api/v1/track2/predict"
TRACK3_VITALDB_URL = f"{os.getenv('TRACK3_URL', 'http://127.0.0.1:8000')}/api/v1/track3/predict"

# Initialize aggregator
aggregator = EnsembleAggregator(CONFIG_PATH)

# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class EnsemblePredictRequest(BaseModel):
    """
    Combined input for all three tracks.
    Patient provides all data at once; backend routes to appropriate tracks.
    """
    patient_id: Optional[str] = Field(None, description="Unique patient identifier")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of observation")
    
    # Track 1 inputs (eICU mortality) - MUST BE Dict[str, Any] to accept strings like gender
    track1_features: Optional[Dict[str, Any]] = Field(
        None, description="562 pre-aggregated features for Track 1 eICU mortality"
    )

    # Track 2 inputs (Multimorbidity — MIMIC + Pima)
    track2_features: Optional[Dict[str, Any]] = Field(
        None, description="6 leak-free features for Track 2 (MIMIC+Pima)"
    )

    # Track 3 inputs (VitalDB waveforms)
    track3_signals: Optional[Dict[str, List[float]]] = Field(
        None, description="Raw physiological signals for Track 3 VitalDB"
    )
    track3_features: Optional[Dict[str, Any]] = Field(
        None, description="Pre-extracted 26 features for Track 3 VitalDB"
    )

class SHAPFeature(BaseModel):
    feature: str
    shap_value: float
    direction: str

class EnsemblePredictResponse(BaseModel):
    """Phase 7 compliant unified ensemble output."""
    patient_id: Optional[str]
    timestamp: str
    overall_risk: Literal["CRITICAL", "HIGH", "MODERATE", "LOW"]  # fixed: added CRITICAL
    risk_score: float = Field(..., ge=0.0, le=1.0)
    track_results: Dict[str, Dict]
    unified_alert: str
    top_features: List[Union[str, SHAPFeature]]
    model_versions: Dict[str, str]
    processing_time_ms: float


# ============================================================================
# ENSEMBLE ENDPOINTS
# ============================================================================

@router.post("/predict", response_model=EnsemblePredictResponse, status_code=status.HTTP_200_OK)
async def predict_ensemble(
    request: EnsemblePredictRequest,
    background_tasks: BackgroundTasks
):
    """
    Main ensemble endpoint.
    Routes Pydantic inputs to the correct backend track services.
    """
    start_time = asyncio.get_event_loop().time()

    if not any([request.track1_features, request.track2_features, request.track3_signals or request.track3_features]):
        raise HTTPException(status_code=400, detail="At least one track's input data must be provided")
    track_tasks = []
    track_names = []

    # -------------------------------------------------------------------------
    # Track 1 — eICU mortality
    # -------------------------------------------------------------------------
    if request.track1_features:
        track1_payload = request.track1_features.copy()
        
        # CRITICAL FALLBACK: eICU router requires gender and ethnicity strings
        if "gender" not in track1_payload:
            track1_payload["gender"] = "Female"
        if "ethnicity" not in track1_payload:
            track1_payload["ethnicity"] = "Caucasian"

        if request.patient_id:
            track1_payload["patient_id"] = request.patient_id
        if request.timestamp:
            track1_payload["observation_window_hours"] = 24

        track_tasks.append(_call_track_api(TRACK1_EICU_URL, track1_payload, "track1_eicu"))
        track_names.append("track1_eicu")

    # -------------------------------------------------------------------------
    # Track 2 — Multimorbidity (MIMIC + Pima)
    # -------------------------------------------------------------------------
    if request.track2_features:
        track2_payload = request.track2_features.copy()
        if request.patient_id:
            track2_payload["patient_id"] = request.patient_id

        track_tasks.append(_call_track_api(TRACK2_MIMIC_URL, track2_payload, "track2_multimorbidity"))
        track_names.append("track2_multimorbidity")

    # -------------------------------------------------------------------------
    # Track 3 — VitalDB waveforms
    # -------------------------------------------------------------------------
    if request.track3_signals or request.track3_features:
        track3_payload = {}
        if request.track3_signals:
            track3_payload["signals"] = request.track3_signals
        if request.track3_features:
            track3_payload["features"] = request.track3_features
        if request.patient_id:
            track3_payload["patient_id"] = request.patient_id

        track_tasks.append(_call_track_api(TRACK3_VITALDB_URL, track3_payload, "track3_vitaldb"))
        track_names.append("track3_vitaldb")

    try:
        results = await asyncio.gather(*track_tasks, return_exceptions=True)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Track services unavailable: {str(e)}")

    track_outputs = {}
    for name, result in zip(track_names, results):
        if isinstance(result, Exception):
            raise HTTPException(status_code=502, detail=f"{name} service failed: {str(result)}")
        track_outputs[name] = result

    try:
        ensemble_result = aggregator.aggregate(
            track1_output=track_outputs.get("track1_eicu", {}),
            track2_output=track_outputs.get("track2_multimorbidity", {}),
            track3_output=track_outputs.get("track3_vitaldb", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble aggregation failed: {str(e)}")

    processing_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

    model_versions = {
        "track1_eicu": track_outputs.get("track1_eicu", {}).get("model_version", "unknown"),
        "track2_multimorbidity": track_outputs.get("track2_multimorbidity", {}).get("model_version", "unknown"),
        "track3_vitaldb": track_outputs.get("track3_vitaldb", {}).get("model_used", "unknown"),
    }
    model_versions = {k: v for k, v in model_versions.items() if k in track_outputs}
    
    # =========================================================================
    # LOG TO SHARED DATABASE FOR HISTORY ENDPOINT
    # =========================================================================
    try:
        # NEW: Combine all track inputs into a single features dict for re-run comparison
        combined_features = {}
        if request.track1_features:
            combined_features["track1_eicu"] = request.track1_features
        if request.track2_features:
            combined_features["track2_multimorbidity"] = request.track2_features
        if request.track3_features or request.track3_signals:
            combined_features["track3_vitaldb"] = request.track3_features or {"signals": request.track3_signals}

        log_prediction(
            request_id=str(uuid.uuid4()),  # Generate a unique ID for this ensemble call
            track_id="ensemble_unified",
            probability=ensemble_result["risk_score"],
            risk_tier=ensemble_result["risk_tier"],
            patient_id=request.patient_id,
            features_json=combined_features,  
            latency_ms=processing_time_ms,
            model_version="ensemble_v1.0.0",
            prediction_json=ensemble_result
        )
    except Exception as e:
        print(f"Failed to log ensemble prediction to DB: {e}")
    # =========================================================================
    # INGEST VITAL SIGNS FOR TIME-SERIES HISTORY
    # =========================================================================
    try:
        from backend_shared.db.database import get_db_session
        from backend_shared.db.models import VitalSignsHistory
        
        # Extract vitals from Track 3 features if available
        track3_feats = request.track3_features or {}
        if track3_feats and request.patient_id:
            vitals_entry = VitalSignsHistory(
                patient_id=request.patient_id,
                timestamp=datetime.now(timezone.utc),
                hr=track3_feats.get("mean_hr"),
                map_val=track3_feats.get("mean_map"),
                spo2=track3_feats.get("mean_spo2"),
            )
            with get_db_session() as db:
                db.add(vitals_entry)
                db.commit()
    except Exception as e:
        print(f"Failed to ingest vital signs: {e}")
    # =========================================================================
    # STANDARDIZE SHAP RESPONSE FOR FRONTEND COMPATIBILITY
    # =========================================================================
    standardized_features = []
    raw_features = ensemble_result.get("top_features", [])
    
    if raw_features:
        # If features are already objects (from Track 1), keep them
        if isinstance(raw_features[0], dict):
            standardized_features = raw_features
        else:
            # If features are strings (from Track 2/3/Ensemble), convert to objects
            # We assign dummy weights for visualization since the backend only returned names
            weight = 1.0
            for i, feature_name in enumerate(raw_features):
                standardized_features.append({
                    "feature": str(feature_name),
                    "shap_value": round(weight, 4),
                    "direction": "increases_risk" # Default assumption for top drivers
                })
                weight -= 0.1 # Decrement for visual hierarchy

    # =========================================================================
    # TRIGGER WEBSOCKET ALERTS (Task 4.2 Integration)
    # =========================================================================
    if ensemble_result["risk_tier"] in ["HIGH", "CRITICAL"] and request.patient_id:
        try:
            await publish_high_risk(request.patient_id, ensemble_result["risk_score"])
        except Exception as e:
            print(f"WebSocket alert failed: {e}")
            
    return EnsemblePredictResponse(
        patient_id=request.patient_id,
        timestamp=request.timestamp or datetime.now(timezone.utc).isoformat(),
        overall_risk=ensemble_result["risk_tier"],
        risk_score=ensemble_result["risk_score"],
        track_results=track_outputs,
        unified_alert=ensemble_result["alert"],
        top_features=standardized_features, # Use the standardized list here
        model_versions=model_versions,
        processing_time_ms=round(processing_time_ms, 2)
    )

@router.post("/predict/track1")
async def predict_track1(payload: Dict):
    return await _call_track_api(VITALDB_URL, payload, "track1_waveform")


@router.post("/predict/track2")
async def predict_track2(payload: Dict):
    return await _call_track_api(MIMIC_URL, payload, "track2_multimorbidity")


@router.post("/predict/track3")
async def predict_track3(payload: Dict):
    return await _call_track_api(EICU_URL, payload, "track3_mortality")


@router.get("/health")
async def ensemble_health():
    """Check health of ensemble service and all track services."""
    health_status = {
        "ensemble": "healthy",
        "tracks": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    track_urls = {
    "track1_eicu": f"{os.getenv('TRACK1_URL', 'http://127.0.0.1:8000')}/api/v1/track1/health",
    "track2_multimorbidity": f"{os.getenv('TRACK2_URL', 'http://127.0.0.1:8000')}/api/v1/track2/health",
    "track3_vitaldb": f"{os.getenv('TRACK3_URL', 'http://127.0.0.1:8000')}/api/v1/track3/health",
    }
    for name, url in track_urls.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                health_status["tracks"][name] = (
                    "healthy" if response.status_code == 200 else "unhealthy"
                )
        except Exception:
            health_status["tracks"][name] = "unreachable"
    return health_status

# ============================================================================
# REGISTRY ENDPOINTS (Task 3.3)
# ============================================================================

@registry_router.get("/loaded")
def get_loaded():
    """List which tracks have models loaded in memory."""
    return {"loaded": list_loaded()}


@registry_router.get("/{track_id}/active")
def get_active(track_id: str):
    """Return the active model version metadata for a track."""
    meta = get_active_version(track_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"No active version for {track_id}")
    return meta


@registry_router.get("/{track_id}/versions")
def get_versions(track_id: str):
    """List all registered versions for a track."""
    return {"track_id": track_id, "versions": list_versions(track_id)}


class RegisterRequest(BaseModel):
    version: str
    model_type: str
    artifact_path: str
    performance_metrics: Optional[dict] = None
    notes: Optional[str] = None
    status: str = "staging"


@registry_router.post("/{track_id}/register")
def register(track_id: str, body: RegisterRequest):
    """Register a new model version (staging by default)."""
    record_id = register_model(
        track_id=track_id,
        version=body.version,
        model_type=body.model_type,
        artifact_path=body.artifact_path,
        performance_metrics=body.performance_metrics,
        notes=body.notes,
        status=body.status,
    )
    return {"status": "registered", "id": record_id}


@registry_router.post("/{track_id}/promote/{version}")
def promote(track_id: str, version: str):
    """Promote a staging version to active (archives current active)."""
    success = promote_to_active(track_id, version)
    if not success:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"status": "promoted", "track_id": track_id, "version": version}


class HotSwapRequest(BaseModel):
    version: str


@registry_router.post("/{track_id}/hot-swap")
def hot_swap_model(track_id: str, body: HotSwapRequest):
    """Hot-swap a track to a new model version without API restart."""
    success = hot_swap(track_id, body.version)
    if not success:
        raise HTTPException(status_code=500, detail="Hot-swap failed — check logs")
    return {"status": "swapped", "track_id": track_id, "new_version": body.version}

# ============================================================================
# DRIFT ENDPOINTS (Task 3.2)
# ============================================================================

@drift_router.post("/run")
def trigger_drift_check():
    """Manually trigger a full drift detection cycle across all tracks."""
    reports = run_drift_cycle(window_minutes=60)
    summary = {
        t: {
            "status": r.get("status"),
            "alert": r.get("alert"),
            "retrain_trigger": r.get("retrain_trigger"),
            "max_psi": r.get("max_psi"),
            "features_drifted": r.get("features_drifted"),
        }
        for t, r in (reports or {}).items()
    }
    return {"summary": summary}


@drift_router.get("/{track_id}")
def drift_status(track_id: str):
    """Run and return drift check report for a single track."""
    return check_drift_for_track(track_id)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _call_track_api(url: str, payload: Dict, track_name: str) -> Dict:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise Exception(f"{track_name} service timeout")
    except httpx.ConnectError:
        raise Exception(f"{track_name} service unreachable at {url}")
    except httpx.HTTPStatusError as e:
        raise Exception(f"{track_name} service error: {e.response.status_code} - {e.response.text}")