# backend_shared/db/logger.py
"""Async-safe logging utilities for predictions and drift metrics."""
from typing import Dict, Optional
from .database import get_db_session
from .models import PredictionLog, DriftMetric
from datetime import datetime, timezone

def log_prediction(
    request_id: str,
    track_id: str,
    probability: float,
    risk_tier: str,
    patient_id: Optional[str] = None,
    features_json: Optional[Dict] = None,
    latency_ms: Optional[float] = None,
    model_version: Optional[str] = None,
    prediction_json: Optional[dict] = None 
) -> int:
    """Log a single inference prediction to the database. Returns the new entry ID."""
    with get_db_session() as db:
        entry = PredictionLog(
            request_id=request_id,
            patient_id=patient_id,
            track_id=track_id,
            probability=probability,
            risk_tier=risk_tier,
            features_json=features_json,
            latency_ms=latency_ms,
            model_version=model_version,
            prediction_json=prediction_json
        )
        db.add(entry)
        db.flush()  # Flush to assign ID without committing
        entry_id = entry.id
        # Commit happens automatically via context manager
        return entry_id

def log_drift_metric(
    track_id: str,
    feature_name: str,
    psi_score: float,
    ks_statistic: Optional[float] = None,
    p_value: Optional[float] = None,
    alert_flag: bool = False,
    sample_size: Optional[int] = None
) -> int:
    """Log a drift detection result to the database. Returns the new entry ID."""
    with get_db_session() as db:
        entry = DriftMetric(
            track_id=track_id,
            feature_name=feature_name,
            psi_score=psi_score,
            ks_statistic=ks_statistic,
            p_value=p_value,
            alert_flag=alert_flag,
            sample_size=sample_size
        )
        db.add(entry)
        db.flush()
        entry_id = entry.id
        return entry_id

def batch_log_drift_metrics(track_id: str, metrics: list[Dict]) -> int:
    """Batch insert multiple drift metrics for performance. Returns count inserted."""
    with get_db_session() as db:
        entries = [DriftMetric(track_id=track_id, **m) for m in metrics]
        db.add_all(entries)
        db.flush()
        return len(entries)