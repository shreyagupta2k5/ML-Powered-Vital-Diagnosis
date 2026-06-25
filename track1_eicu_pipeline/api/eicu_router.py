"""
eicu_router.py — FastAPI endpoints for Track 1 eICU Mortality Prediction
Author: Shreya Gupta

Endpoints
---------
GET  /api/v1/track1/health     → model / service health check
POST /api/v1/track1/predict    → ICU mortality probability + risk tier + SHAP drivers

Usage (from project root)
---------
    uvicorn track1_eicu_pipeline.api.eicu_router:app --reload --port 8003
"""

from __future__ import annotations

import csv
import json
import logging
import os
import pathlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

import numpy as np
import pandas as pd

# ── FastAPI ──────────────────────────────────────────────────────────────────
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Project schemas ──────────────────────────────────────────────────────────
from track1_eicu_pipeline.api.schemas import (
    HealthResponse,
    PredictRequest,
    PredictResponse,
    SHAPDriver,
)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS  (resolve relative to this file so it works from any working directory)
# ─────────────────────────────────────────────────────────────────────────────

_HERE = pathlib.Path(__file__).resolve().parent          # …/track1_eicu_pipeline/api/
_ROOT = _HERE.parent                                     # …/track1_eicu_pipeline/

MODEL_PATH        = _ROOT / "models" / "track1_best_model.pkl"
FEATURE_COLS_PATH = _ROOT / "metadata" / "feature_columns.csv"
LOG_DIR           = _ROOT / "logs"
LOG_PATH          = LOG_DIR / "predictions.csv"

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
# logger = logging.getLogger("track3.eicu_router")
logger = logging.getLogger("track1.eicu_router")

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# MODEL_VERSION     = "track3_random_forest_v1.0"
MODEL_VERSION = "track1_random_forest_v1.0"
ALERT_THRESHOLD   = 0.15          # from notebook: recommended balanced threshold

# Risk-tier thresholds (aligned with clinical_decision_summary.csv)
TIER_HIGH     = 0.30
TIER_MODERATE = 0.15

ACTIONS = {
    "HIGH":     "⚠️  IMMEDIATE REVIEW — Escalate to intensivist. "
                "High probability of ICU mortality. Reassess every 1 h.",
    "MODERATE": "🔶 CLOSE MONITORING — Re-evaluate within 2 h. "
                "Consider additional labs and senior review.",
    "LOW":      "✅ ROUTINE MONITORING — Continue standard ICU observations. "
                "Reassess at next scheduled round.",
}

# CSV columns written to predictions.log
LOG_COLUMNS = [
    "timestamp_utc",
    "request_id",
    "patient_id",
    "observation_window_hours",
    "mortality_probability",
    "risk_tier",
    "latency_ms",
    "model_version",
    "top_feature_1",
    "top_shap_1",
    "top_feature_2",
    "top_shap_2",
    "top_feature_3",
    "top_shap_3",
]

# ─────────────────────────────────────────────────────────────────────────────
# MODEL + FEATURE LOADING  (done once at import time)
# ─────────────────────────────────────────────────────────────────────────────

_model       = None
_feature_cols: List[str] = []
_shap_explainer = None


def _load_artifacts() -> None:
    global _model, _feature_cols, _shap_explainer

    # ─ feature columns ──────────────────────────────────────────────────────
    if FEATURE_COLS_PATH.exists():
        df = pd.read_csv(FEATURE_COLS_PATH)
        # FIX: Skip header row if present, take only actual column names
        col_list = df.iloc[:, 0].tolist()
        # Remove any non-feature entries (like "0" header artifact)
        _feature_cols = [c for c in col_list if isinstance(c, str) and c.strip()]
        logger.info("Loaded %d feature columns from %s", len(_feature_cols), FEATURE_COLS_PATH)
    else:
        logger.warning("feature_columns.csv not found — features will be inferred.")

    # ─ model ─────────────────────────────────────────────────────────────────
    if MODEL_PATH.exists():
        import joblib
        try:
            _model = joblib.load(MODEL_PATH)
            # Verify feature count matches
            expected = getattr(_model, 'n_features_in_', None)
            if expected and expected != len(_feature_cols):
                logger.error(
                    "FEATURE MISMATCH: Model expects %d features but CSV has %d. "
                    "Predictions will be WRONG.", expected, len(_feature_cols)
                )
            logger.info("Model loaded from %s (expects %d features)", MODEL_PATH, expected)
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            _model = None
    else:
        logger.error("Model file not found at %s", MODEL_PATH)

    # ── SHAP explainer ───────────────────────────────────────────────────────
    try:
        import shap
        if _model is not None:
            estimator = _model
            if hasattr(_model, "named_steps"):
                estimator = _model.named_steps.get(
                    "clf", list(_model.named_steps.values())[-1]
                )
            _shap_explainer = shap.TreeExplainer(estimator)
            logger.info("SHAP TreeExplainer initialised")
    except Exception as exc:
        logger.warning("SHAP explainer not available: %s", exc)
        _shap_explainer = None

_load_artifacts()

# ─────────────────────────────────────────────────────────────────────────────
# LOG SETUP  (append-only CSV; create with header on first run)
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_log_file() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        with open(LOG_PATH, "w", newline="") as fh:
            csv.DictWriter(fh, fieldnames=LOG_COLUMNS).writeheader()
        logger.info("Created prediction log at %s", LOG_PATH)


_ensure_log_file()


def _write_log(row: Dict[str, Any]) -> None:
    try:
        with open(LOG_PATH, "a", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=LOG_COLUMNS)
            writer.writerow({k: row.get(k, "") for k in LOG_COLUMNS})
    except Exception as exc:
        logger.warning("Failed to write prediction log: %s", exc)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: build feature DataFrame from request
# ─────────────────────────────────────────────────────────────────────────────

def _build_feature_df(req: PredictRequest) -> pd.DataFrame:
    """
    Build feature DataFrame aligned EXACTLY to model's expected 561 columns.
    Missing features are imputed to 0.0 (same as training).
    """
    excluded = {"patient_id", "observation_window_hours", "extra_features"}
    
    # 1. Extract declared fields
    flat = {
        k: v for k, v in req.model_dump(exclude=excluded).items()
        if v is not None
    }
    
    # 2. Merge extra_features
    if req.extra_features:
        flat.update({k: v for k, v in req.extra_features.items() if v is not None})
    
    # 3. Absorb pydantic extra fields
    if req.__pydantic_extra__:
        for k, v in req.__pydantic_extra__.items():
            if k not in excluded and v is not None:
                flat[k] = v
    
    # 4. Build DataFrame
    df = pd.DataFrame([flat])
    
    # 5. CRITICAL FIX: Align to EXACT model feature count
    if _feature_cols:
        # Use ONLY the first N columns that match model expectation
        target_cols = _feature_cols[:getattr(_model, 'n_features_in_', len(_feature_cols))]
        
        # Add missing columns with 0.0
        for col in target_cols:
            if col not in df.columns:
                df[col] = 0.0
        
        # Select ONLY target columns in exact order
        df = df[target_cols]
        
        # Log warning if we're dropping columns
        if len(_feature_cols) > len(target_cols):
            dropped = set(_feature_cols) - set(target_cols)
            logger.warning(
                "Dropped %d excess features to match model's %d expected: %s",
                len(dropped), len(target_cols), list(dropped)[:5]
            )
    
    return df

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: encode categoricals so SHAP gets a fully numeric array
# ─────────────────────────────────────────────────────────────────────────────

def _encode_for_shap(df_row: pd.DataFrame) -> tuple:
    """
    One-hot encode gender/ethnicity and return (numeric_array, feature_names).
    This matches the encoding done during training (SMOTETomek pipeline).
    """
    df = df_row.copy()

    cat_cols = [c for c in ["gender", "ethnicity"] if c in df.columns]
    num_cols = [c for c in df.columns if c not in cat_cols]

    # Numeric part
    X_num = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    names = list(num_cols)

    # Categorical part — simple pandas get_dummies to match training encoding
    if cat_cols:
        dummies = pd.get_dummies(df[cat_cols], prefix=cat_cols).astype(float)
        X_enc = pd.concat([X_num, dummies], axis=1)
        names = list(X_enc.columns)
    else:
        X_enc = X_num

    return X_enc.values, names


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: compute SHAP top-5 drivers (per-patient)
# ─────────────────────────────────────────────────────────────────────────────

def _get_shap_drivers(
    df_row: pd.DataFrame,
    feature_names: List[str],
    n: int = 5,
) -> List[SHAPDriver]:
    """
    Returns top-n signed per-patient SHAP values.
    Encodes categoricals first so TreeExplainer always receives a numeric array.
    Falls back to global feature_importances_ only if SHAP is unavailable.
    """
    drivers: List[SHAPDriver] = []

    if _shap_explainer is not None:
        try:
            X_arr, enc_names = _encode_for_shap(df_row)

            # TreeExplainer expects (n_samples, n_features) matching training
            # The model was trained on encoded data — align column count
            estimator = _model
            if hasattr(_model, "named_steps"):
                estimator = list(_model.named_steps.values())[-1]

            n_features_model = estimator.n_features_in_
            if X_arr.shape[1] < n_features_model:
                # Pad missing columns with zeros
                pad = np.zeros((1, n_features_model - X_arr.shape[1]))
                X_arr = np.hstack([X_arr, pad])
                enc_names += [f"__pad_{i}" for i in range(pad.shape[1])]
            elif X_arr.shape[1] > n_features_model:
                X_arr = X_arr[:, :n_features_model]
                enc_names = enc_names[:n_features_model]

            shap_vals = _shap_explainer.shap_values(X_arr)

            # shap_values → list[class0, class1] for RandomForest classifier
            if isinstance(shap_vals, list) and len(shap_vals) == 2:
                sv = shap_vals[1][0]   # class-1 (expired) for first row
            elif isinstance(shap_vals, np.ndarray) and shap_vals.ndim == 3:
                sv = shap_vals[0, :, 1]
            else:
                sv = np.array(shap_vals).flatten()

            pairs = sorted(zip(enc_names, sv), key=lambda x: abs(x[1]), reverse=True)

            for fname, fval in pairs[:n]:
                if fname.startswith("__pad_"):
                    continue
                drivers.append(
                    SHAPDriver(
                        feature=fname,
                        shap_value=round(float(fval), 5),
                        direction="increases_risk" if fval > 0 else "decreases_risk",
                    )
                )

            if drivers:
                logger.debug("Per-patient SHAP computed for %d features", len(sv))
                return drivers

        except Exception as exc:
            logger.warning("Per-patient SHAP failed, falling back: %s", exc)

    # ── Fallback: global feature_importances_ with actual input values ────────
    try:
        estimator = _model
        if hasattr(_model, "named_steps"):
            estimator = list(_model.named_steps.values())[-1]
        importances = estimator.feature_importances_
        top_idx = np.argsort(importances)[::-1][:n]
        for i in top_idx:
            fname = feature_names[i] if i < len(feature_names) else f"feature_{i}"
            drivers.append(
                SHAPDriver(
                    feature=fname,
                    shap_value=round(float(importances[i]), 5),
                    direction="increases_risk",   # direction unknown without SHAP
                )
            )
    except Exception:
        pass

    return drivers

# ─────────────────────────────────────────────────────────────────────────────
# RISK-TIER LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _risk_tier(prob: float) -> str:
    if prob >= TIER_HIGH:
        return "HIGH"
    if prob >= TIER_MODERATE:
        return "MODERATE"
    return "LOW"

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

# router = APIRouter(prefix="/api/v1/track3", tags=["Track 3 — eICU Mortality"])
router = APIRouter(
    prefix="/api/v1/track1",
    tags=["Track 1 — eICU Mortality"]
)


# ── Health check ──────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service and model health check",
)
async def health_check() -> HealthResponse:
    """
    Returns current model load status, feature count, and version.
    Use this before sending predictions to confirm the service is ready.
    """
    loaded = _model is not None
    return HealthResponse(
        status="ok" if loaded else "unavailable",
        model_loaded=loaded,
        model_version=MODEL_VERSION,
        feature_count=len(_feature_cols),
        message=(
            "Model ready. Send POST /api/v1/track1/predict to score a patient."
            if loaded
            else f"Model not loaded. Expected file: {MODEL_PATH}"
        ),
    )


# ── Predict ───────────────────────────────────────────────────────────────────

@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="ICU mortality prediction with risk tier and SHAP explanations",
    responses={
        503: {"description": "Model not loaded"},
        422: {"description": "Validation error in input features"},
    },
)
async def predict(req: PredictRequest) -> PredictResponse:
    """
    Predict ICU mortality probability for a single patient stay.

    **Input:** 562 pre-aggregated features (24 h observation window by default).
    Declare common vitals/labs in the top-level fields; pass the remaining
    columns via the `extra_features` dict.

    **Output:**
    - `mortality_probability` — calibrated score (0 – 1)
    - `risk_tier` — HIGH / MODERATE / LOW
    - `recommended_action` — clinical guidance string
    - `top_shap_drivers` — top-5 signed SHAP feature contributions
    """
    if _model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not loaded. Expected at: {MODEL_PATH}",
        )

    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())

    # ── 1. Build feature DataFrame ────────────────────────────────────────────
    try:
        df_row = _build_feature_df(req)
    except Exception as exc:
        logger.error("Feature assembly failed for request %s: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Feature assembly error: {exc}",
        )

    # ── 2. Predict ────────────────────────────────────────────────────────────
    try:
        prob: float = float(_model.predict_proba(df_row)[0, 1])
    except Exception as exc:
        logger.error("Model inference failed for request %s: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model inference error: {exc}",
        )

    tier   = _risk_tier(prob)
    action = ACTIONS[tier]

    # ── 3. SHAP drivers ───────────────────────────────────────────────────────
    feature_names = _feature_cols if _feature_cols else list(df_row.columns)
    drivers = _get_shap_drivers(df_row, feature_names, n=5)

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # ── 4. Telemetry log ──────────────────────────────────────────────────────
    log_row: Dict[str, Any] = {
        "timestamp_utc":           datetime.now(timezone.utc).isoformat(),
        "request_id":              request_id,
        "patient_id":              req.patient_id or "",
        "observation_window_hours": req.observation_window_hours or 24,
        "mortality_probability":   round(prob, 6),
        "risk_tier":               tier,
        "latency_ms":              latency_ms,
        "model_version":           MODEL_VERSION,
    }
    for i, d in enumerate(drivers[:3], start=1):
        log_row[f"top_feature_{i}"] = d.feature
        log_row[f"top_shap_{i}"]    = d.shap_value

    _write_log(log_row)

    logger.info(
        "request_id=%s patient_id=%s prob=%.4f tier=%s latency=%.1f ms",
        request_id, req.patient_id, prob, tier, latency_ms,
    )

    # ── 5. Response ───────────────────────────────────────────────────────────
    return PredictResponse(
        patient_id=req.patient_id,
        mortality_probability=round(prob, 6),
        risk_tier=tier,
        recommended_action=action,
        top_shap_drivers=drivers,
        model_version=MODEL_VERSION,
        observation_window_hours=req.observation_window_hours or 24,
        alert_threshold_used=ALERT_THRESHOLD,
    )


# ─────────────────────────────────────────────────────────────────────────────
# APP FACTORY  (used when running standalone via uvicorn)
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        # title="Track 3 — eICU Mortality Prediction API,"
        title="Track 1 — eICU Mortality Prediction API",
        description=(
            "ML-powered ICU mortality early-warning system built on the "
            "eICU Collaborative Research Database. "
            "Models: Random Forest (AUC 0.8076) | XGBoost (AUC 0.7834). "
            "Threshold 0.15 → balanced clinical use; 0.30 → best F1."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root():
        # return {
        #     "service":  "Track 3 eICU Mortality Prediction",
        #     "health":   "/api/v1/track3/health",
        #     "predict":  "/api/v1/track3/predict",
        #     "docs":     "/docs",
        # }
        return {
            "service": "Track 1 eICU Mortality Prediction",
            "health": "/api/v1/track1/health",
            "predict": "/api/v1/track1/predict",
            "docs": "/docs",
        }

    return app


# Allow `uvicorn track3_eicu_pipeline.api.eicu_router:app`
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eicu_router:app", host="0.0.0.0", port=8003, reload=True)