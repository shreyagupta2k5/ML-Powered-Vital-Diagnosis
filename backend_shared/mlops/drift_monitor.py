# backend_shared/mlops/drift_monitor.py
"""
Unified Drift Monitoring Service — Task 3.2
Centralizes PSI + KS drift detection across all 3 tracks.
Runs every 10 minutes (configurable via drift_thresholds.json).
"""
import json
import logging
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config paths ─────────────────────────────────────────────────────────────
_ROOT = pathlib.Path(__file__).resolve().parent.parent          # backend_shared/
_CONFIG_PATH = _ROOT / "config" / "drift_thresholds.json"

def _load_config() -> Dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    # Sensible defaults if file is missing
    return {
        "global": {
            "psi_alert": 0.25, "psi_critical": 0.50,
            "ks_p_value_threshold": 0.05,
            "min_features_for_alert": 3,
            "run_interval_minutes": 10
        }
    }


# ── PSI & KS helpers ─────────────────────────────────────────────────────────

def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
    epsilon: float = 1e-6
) -> float:
    """
    Population Stability Index (PSI).
    PSI < 0.10  → no significant drift
    PSI 0.10-0.25 → slight shift (warning)
    PSI > 0.25  → significant drift (alert)
    PSI > 0.50  → critical drift
    """
    # Build shared bin edges from reference
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bins = np.linspace(min_val, max_val, n_bins + 1)

    ref_counts, _ = np.histogram(reference, bins=bins)
    cur_counts, _ = np.histogram(current, bins=bins)

    ref_pct = (ref_counts / len(reference)) + epsilon
    cur_pct = (cur_counts / len(current)) + epsilon

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return float(psi)


def compute_ks(
    reference: np.ndarray,
    current: np.ndarray
) -> Tuple[float, float]:
    """KS two-sample test. Returns (statistic, p_value)."""
    stat, p_value = stats.ks_2samp(reference, current)
    return float(stat), float(p_value)


# ── Feature extraction helpers ────────────────────────────────────────────────

def _get_reference_data(track_id: str) -> Optional[pd.DataFrame]:
    """
    Load reference (training) distribution for a given track.
    Looks for a parquet or CSV reference file saved during training.
    Returns None if not found (drift check is skipped gracefully).
    """
    candidates = [
        _ROOT.parent / f"{track_id}" / "data" / "reference_distribution.parquet",
        _ROOT.parent / f"{track_id}" / "data" / "reference_distribution.csv",
        _ROOT / "mlops" / "reference" / f"{track_id}_reference.parquet",
        _ROOT / "mlops" / "reference" / f"{track_id}_reference.csv",
    ]
    for path in candidates:
        if path.exists():
            logger.info(f"[{track_id}] Loaded reference data from {path}")
            return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    logger.warning(f"[{track_id}] No reference data found — skipping drift check.")
    return None


def _get_recent_predictions(track_id: str, window_minutes: int = 60) -> Optional[pd.DataFrame]:
    """
    Pull recent prediction feature vectors from the DB (last `window_minutes`).
    Falls back to CSV logs if DB is unavailable.
    """
    try:
        from backend_shared.db.database import get_db_session
        from backend_shared.db.models import PredictionLog
        from sqlalchemy import select

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        with get_db_session() as db:
            rows = db.query(PredictionLog).filter(
                PredictionLog.track_id == track_id,
                PredictionLog.timestamp >= cutoff,
                PredictionLog.features_json.isnot(None)
            ).all()

        if not rows:
            logger.debug(f"[{track_id}] No DB rows found, falling back to CSV.")
            return _get_recent_predictions_from_csv(track_id, window_minutes)

        records = [r.features_json for r in rows if isinstance(r.features_json, dict)]
        if not records:
            return _get_recent_predictions_from_csv(track_id, window_minutes)
        return pd.DataFrame(records)

    except Exception as e:
        logger.warning(f"[{track_id}] DB query failed ({e}), falling back to CSV logs.")
        return _get_recent_predictions_from_csv(track_id, window_minutes)

def _get_recent_predictions_from_csv(track_id: str, window_minutes: int) -> Optional[pd.DataFrame]:
    """Fallback: read features from CSV log files."""
    # Primary: use current data simulation files
    csv_candidates = {
        "track1_eicu": _ROOT / "mlops" / "reference" / "track1_eicu_current.csv",
        "track2_multimorbidity": _ROOT / "mlops" / "reference" / "track2_multimorbidity_current.csv",
        "track3_vitaldb": _ROOT / "mlops" / "reference" / "track3_vitaldb_current.csv",
    }
    # Fallback: original log files
    fallback_candidates = {
        "track1_eicu": _ROOT.parent / "track1_eicu_pipeline" / "logs" / "predictions.csv",
        "track2_multimorbidity": _ROOT.parent / "track2_multimorbidity" / "inference" / "logs" / "api_inference_logs.csv",
        "track3_vitaldb": _ROOT.parent / "vitalDB project" / "logs" / "predictions.csv",
    }

    path = csv_candidates.get(track_id)
    if not path or not path.exists():
        path = fallback_candidates.get(track_id)

    if path and path.exists():
        df = pd.read_csv(path, on_bad_lines='skip')
        df = df.select_dtypes(include='number')
        return df if not df.empty else None
    return None


# ── Track feature configs ─────────────────────────────────────────────────────

TRACK_FEATURE_CONFIG = {
    "track1_eicu": {
        "features": ["observation_window_hours", "mortality_probability", "latency_ms"],
    },
    "track2_multimorbidity": {
        "features": ["glucose_mean", "glucose_min", "glucose_max", "glucose_std", "glucose_cv", "glucose_count"],
    },
    "track3_vitaldb": {
        "features": ["ECG", "HR", "MAP", "SPO2"],
    },
}


def _resolve_features(track_id: str, reference_df: pd.DataFrame) -> List[str]:
    """Return the list of features to monitor for a given track."""
    cfg = TRACK_FEATURE_CONFIG.get(track_id, {})

    # Explicit feature list (Track 2)
    if "features" in cfg:
        return [f for f in cfg["features"] if f in reference_df.columns]

    # SHAP-ranked top-N (Tracks 1 & 3)
    shap_file = pathlib.Path(__file__).resolve().parent.parent.parent / cfg.get("shap_file", "")
    if shap_file.exists():
        with open(shap_file) as f:
            shap_importance: Dict[str, float] = json.load(f)
        top_n = cfg.get("top_n", 10)
        ranked = sorted(shap_importance, key=shap_importance.get, reverse=True)[:top_n]
        return [f for f in ranked if f in reference_df.columns]

    # Fallback: all numeric columns in reference
    return reference_df.select_dtypes(include=[np.number]).columns.tolist()


# ── Core drift check ──────────────────────────────────────────────────────────

def check_drift_for_track(
    track_id: str,
    config: Optional[Dict] = None,
    window_minutes: int = 60
) -> Dict:
    """
    Run PSI + KS drift detection for a single track.
    Returns a summary dict with per-feature metrics and an overall alert flag.
    """
    if config is None:
        config = _load_config()

    track_cfg = config.get(track_id, config.get("global", {}))
    global_cfg = config.get("global", {})

    psi_alert = track_cfg.get("psi_alert", global_cfg.get("psi_alert", 0.25))
    psi_critical = track_cfg.get("psi_critical", global_cfg.get("psi_critical", 0.50))
    min_features = track_cfg.get("min_features_for_alert", global_cfg.get("min_features_for_alert", 3))
    ks_threshold = global_cfg.get("ks_p_value_threshold", 0.05)

    result = {
        "track_id": track_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "alert": False,
        "retrain_trigger": False,
        "features_checked": 0,
        "features_drifted": 0,
        "max_psi": 0.0,
        "metrics": []
    }

    # 1. Load reference data
    reference_df = _get_reference_data(track_id)
    if reference_df is None:
        result["status"] = "skipped_no_reference"
        return result

    # 2. Load recent production data
    current_df = _get_recent_predictions(track_id, window_minutes)
    if current_df is None or current_df.empty:
        result["status"] = "skipped_no_current_data"
        return result

    # 3. Resolve feature list
    features = _resolve_features(track_id, reference_df)
    if not features:
        result["status"] = "skipped_no_features"
        return result

    result["features_checked"] = len(features)
    metrics = []
    drifted_count = 0
    max_psi = 0.0

    for feature in features:
        if feature not in current_df.columns:
            continue

        ref_vals = reference_df[feature].dropna().to_numpy()
        cur_vals = current_df[feature].dropna().to_numpy()

        if len(ref_vals) < 30 or len(cur_vals) < 10:
            logger.debug(f"[{track_id}] Skipping {feature}: insufficient samples.")
            continue

        # Skip near-constant features — PSI is meaningless on them
        if ref_vals.std() < 1e-6:
            logger.debug(f"[{track_id}] Skipping {feature}: near-constant in reference (std={ref_vals.std():.2e})")
            continue

        psi = compute_psi(ref_vals, cur_vals)
        ks_stat, p_val = compute_ks(ref_vals, cur_vals)
        alert = psi > psi_alert or (p_val < ks_threshold and ks_stat > 0.2)

        if psi > max_psi:
            max_psi = psi
        if alert:
            drifted_count += 1

        metric = {
            "feature_name": feature,
            "psi_score": round(psi, 4),
            "ks_statistic": round(ks_stat, 4),
            "p_value": round(p_val, 6),
            "alert_flag": alert,
            "sample_size": len(cur_vals),
        }
        metrics.append(metric)

        # Persist to DB
        try:
            from backend_shared.db.logger import log_drift_metric
            log_drift_metric(track_id=track_id, **metric)
        except Exception as e:
            logger.debug(f"DB log failed for {feature}: {e}")

    result["metrics"] = metrics
    result["features_drifted"] = drifted_count
    result["max_psi"] = round(max_psi, 4)

    # 4. Evaluate alert / retrain conditions
    if drifted_count >= min_features or max_psi > psi_critical:
        result["alert"] = True
        result["status"] = "drift_detected"

    if drifted_count >= min_features and max_psi > psi_critical:
        result["retrain_trigger"] = True
        result["status"] = "retrain_required"

    logger.info(
        f"[{track_id}] Drift check complete — "
        f"{drifted_count}/{len(features)} features drifted, max_psi={max_psi:.4f}, "
        f"alert={result['alert']}, retrain={result['retrain_trigger']}"
    )
    return result


def run_all_tracks(window_minutes: int = 60) -> Dict[str, Dict]:
    """Run drift checks for all 3 tracks and return a combined report."""
    config = _load_config()
    tracks = ["track1_eicu", "track2_multimorbidity", "track3_vitaldb"]
    report = {}
    for track in tracks:
        try:
            report[track] = check_drift_for_track(track, config, window_minutes)
        except Exception as e:
            logger.error(f"[{track}] Drift check failed: {e}")
            report[track] = {"track_id": track, "status": "error", "error": str(e)}
    return report


if __name__ == "__main__":
    results = run_all_tracks()
    for track, r in results.items():
        print(f"\n{'='*60}")
        print(f"Track: {track}")
        print(f"  Status        : {r.get('status')}")
        print(f"  Alert         : {r.get('alert')}")
        print(f"  Retrain Needed: {r.get('retrain_trigger')}")
        print(f"  Features Drifted: {r.get('features_drifted')}/{r.get('features_checked')}")
        print(f"  Max PSI       : {r.get('max_psi')}")