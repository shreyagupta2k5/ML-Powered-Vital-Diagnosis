# ensemble_layer/api/ensemble_router.py
"""
Ensemble API Gateway — Main entry point for unified risk prediction.
Routes requests to individual tracks, aggregates results, returns Phase 7 compliant output.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal
import httpx
import asyncio
import json
import pathlib
from datetime import datetime, timezone
from ..services.aggregator import EnsembleAggregator
from ..services.risk_scorer import RiskScorer

router = APIRouter(prefix="/api/v1/ensemble", tags=["Ensemble Layer"])

# Configuration
CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config" / "weights.json"

# Track API endpoints (configured via environment or defaults)
TRACK1_URL = "http://localhost:8001/api/v1/track1/predict"
TRACK2_URL = "http://localhost:8002/api/v1/track2/predict"
TRACK3_URL = "http://localhost:8003/api/v1/track3/predict"

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
    
    # Track 1 inputs (VitalDB waveforms)
    track1_signals: Optional[Dict[str, List[float]]] = Field(
        None,
        description="Raw physiological signals for Track 1 (ECG, HR, MAP, SpO2 arrays)"
    )
    track1_features: Optional[Dict[str, float]] = Field(
        None,
        description="Pre-extracted 26 features for Track 1"
    )
    
    # Track 2 inputs (MIMIC+Pima)
    track2_features: Optional[Dict[str, float]] = Field(
        None,
        description="6 leak-free features for Track 2 (glucose_mean, glucose_count, sbp_mean, sbp_count, map_mean, map_count)"
    )
    
    # Track 3 inputs (eICU mortality)
    track3_features: Optional[Dict[str, float]] = Field(
        None,
        description="562 pre-aggregated features for Track 3 (from metadata/feature_columns.csv)"
    )

class EnsemblePredictResponse(BaseModel):
    """Phase 7 compliant unified ensemble output."""
    patient_id: Optional[str]
    timestamp: str
    overall_risk: Literal["HIGH", "MODERATE", "LOW"]
    risk_score: float = Field(..., ge=0.0, le=1.0)
    track_results: Dict[str, Dict]
    unified_alert: str
    top_features: List[str]
    model_versions: Dict[str, str]
    processing_time_ms: float

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/predict", response_model=EnsemblePredictResponse, status_code=status.HTTP_200_OK)
async def predict_ensemble(
    request: EnsemblePredictRequest,
    background_tasks: BackgroundTasks
):
    """
    **Main ensemble endpoint** — Calls all 3 tracks and returns unified risk assessment.
    
    This endpoint:
    1. Validates input contains at least one track's data
    2. Makes async HTTP calls to individual track APIs
    3. Aggregates results using weighted fusion
    4. Returns Phase 7 compliant JSON
    
    **Input:** Combined patient data (waveforms, features, or both)
    **Output:** Unified risk score, tier, alerts, and track-specific results
    """
    start_time = asyncio.get_event_loop().time()
    
    # Validate at least one track has data
    if not any([
        request.track1_signals or request.track1_features,
        request.track2_features,
        request.track3_features
    ]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one track's input data must be provided"
        )
    
    # Prepare track-specific requests
    track_tasks = []
    track_names = []
    
    # Track 1 request
    if request.track1_signals or request.track1_features:
        track1_payload = {}
        if request.track1_signals:
            track1_payload["signals"] = request.track1_signals
        if request.track1_features:
            track1_payload["features"] = request.track1_features
        if request.patient_id:
            track1_payload["patient_id"] = request.patient_id
        
        track_tasks.append(_call_track_api(TRACK1_URL, track1_payload, "track1_waveform"))
        track_names.append("track1_waveform")
    
    # Track 2 request
    if request.track2_features:
        track2_payload = request.track2_features.copy()
        if request.patient_id:
            track2_payload["patient_id"] = request.patient_id
        
        track_tasks.append(_call_track_api(TRACK2_URL, track2_payload, "track2_multimorbidity"))
        track_names.append("track2_multimorbidity")
    
    # Track 3 request
    if request.track3_features:
        track3_payload = {"features": request.track3_features}
        if request.patient_id:
            track3_payload["patient_id"] = request.patient_id
        if request.timestamp:
            track3_payload["observation_window_hours"] = 24  # Default
        
        track_tasks.append(_call_track_api(TRACK3_URL, track3_payload, "track3_mortality"))
        track_names.append("track3_mortality")
    
    # Execute all track predictions concurrently
    try:
        results = await asyncio.gather(*track_tasks, return_exceptions=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"One or more track services unavailable: {str(e)}"
        )
    
    # Check for errors in results
    track_outputs = {}
    for i, (name, result) in enumerate(zip(track_names, results)):
        if isinstance(result, Exception):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{name} service failed: {str(result)}"
            )
        track_outputs[name] = result
    
    # Aggregate results
    try:
        ensemble_result = aggregator.aggregate(
            track1_output=track_outputs.get("track1_waveform", {}),
            track2_output=track_outputs.get("track2_multimorbidity", {}),
            track3_output=track_outputs.get("track3_mortality", {})
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ensemble aggregation failed: {str(e)}"
        )
    
    # Calculate processing time
    processing_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
    
    # Extract model versions from track responses
    model_versions = {}
    if "track1_waveform" in track_outputs:
        model_versions["track1"] = track_outputs["track1_waveform"].get("model_used", "unknown")
    if "track2_multimorbidity" in track_outputs:
        model_versions["track2"] = track_outputs["track2_multimorbidity"].get("model_version", "unknown")
    if "track3_mortality" in track_outputs:
        model_versions["track3"] = track_outputs["track3_mortality"].get("model_version", "unknown")
    
    # Build response
    return EnsemblePredictResponse(
        patient_id=request.patient_id,
        timestamp=request.timestamp or datetime.now(timezone.utc).isoformat(),
        overall_risk=ensemble_result["risk_tier"],
        risk_score=ensemble_result["risk_score"],
        track_results=track_outputs,
        unified_alert=ensemble_result["alert"],
        top_features=ensemble_result["top_features"],
        model_versions=model_versions,
        processing_time_ms=round(processing_time_ms, 2)
    )

@router.post("/predict/track1", tags=["Individual Tracks"])
async def predict_track1(payload: Dict):
    """Route prediction to Track 1 (VitalDB waveforms) only."""
    return await _call_track_api(TRACK1_URL, payload, "track1_waveform")

@router.post("/predict/track2", tags=["Individual Tracks"])
async def predict_track2(payload: Dict):
    """Route prediction to Track 2 (MIMIC+Pima) only."""
    return await _call_track_api(TRACK2_URL, payload, "track2_multimorbidity")

@router.post("/predict/track3", tags=["Individual Tracks"])
async def predict_track3(payload: Dict):
    """Route prediction to Track 3 (eICU mortality) only."""
    return await _call_track_api(TRACK3_URL, payload, "track3_mortality")

@router.get("/health")
async def ensemble_health():
    """Check health of ensemble service and all track services."""
    health_status = {
        "ensemble": "healthy",
        "tracks": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Check each track
    for name, url in [("track1", TRACK1_URL.replace("/predict", "/health")),
                      ("track2", TRACK2_URL.replace("/predict", "/health")),
                      ("track3", TRACK3_URL.replace("/predict", "/health"))]:
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
# HELPER FUNCTIONS
# ============================================================================

async def _call_track_api(url: str, payload: Dict, track_name: str) -> Dict:
    """
    Make async HTTP call to individual track API.
    
    Args:
        url: Track API endpoint URL
        payload: Request payload
        track_name: Name for error reporting
    
    Returns:
        Track API response as dict
    
    Raises:
        HTTPException: If track service unavailable
    """
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