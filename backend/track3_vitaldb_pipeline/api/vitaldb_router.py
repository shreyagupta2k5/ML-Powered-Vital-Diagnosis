from fastapi import APIRouter
from datetime import datetime

import os
import joblib
import pandas as pd

from api.feature_extractor import (
    segment_signals,
    extract_features,
    FEATURE_COLUMNS
)

from mlops.drift_detector import (
    detect_drift
)

router = APIRouter()

# ==========================================
# BASE DIRECTORY
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

# ==========================================
# LOAD MODELS
# ==========================================

hyp_model = joblib.load(
    os.path.join(
        BASE_DIR,
        "models",
        "hypotension",
        "best_model.pkl"
    )
)

tach_model = joblib.load(
    os.path.join(
        BASE_DIR,
        "models",
        "tachycardia",
        "best_model.pkl"
    )
)

spo2_model = joblib.load(
    os.path.join(
        BASE_DIR,
        "models",
        "low_spo2",
        "best_model.pkl"
    )
)

# ==========================================
# LOAD REFERENCE DATASET
# ==========================================

reference_df = pd.read_csv(
    os.path.join(
        BASE_DIR,
        "reference_data",
        "vitaldb_advanced_features.csv"
    )
)

reference_df = reference_df[
    FEATURE_COLUMNS
]

# ==========================================
# API ENDPOINT
# ==========================================

@router.post("/api/v1/track3/predict")
def predict(payload: dict):

    # ======================================
    # CASE 1: PRE-EXTRACTED FEATURES
    # ======================================

    if "features" in payload:

        features_df = pd.DataFrame(
            [payload["features"]]
        )

        features_df = features_df[
            FEATURE_COLUMNS
        ]

    # ======================================
    # CASE 2: RAW SIGNALS
    # ======================================

    else:

        windows = segment_signals(

            payload["ecg"],

            payload["hr"],

            payload["map"],

            payload["spo2"]
        )

        if len(windows) == 0:

            return {
                "error":
                "Signal length must be at least 3000 samples."
            }

        features_df = extract_features(
            windows[0]
        )

    # ======================================
    # MODEL PREDICTIONS
    # ======================================

    hyp_prob = float(

        hyp_model.predict_proba(
            features_df
        )[0][1]
    )

    tach_prob = float(

        tach_model.predict_proba(
            features_df
        )[0][1]
    )

    spo2_prob = float(

        spo2_model.predict_proba(
            features_df
        )[0][1]
    )

    # ======================================
    # RISK SCORE
    # ======================================

    risk_score = (

        0.5 * hyp_prob +

        0.2 * tach_prob +

        0.3 * spo2_prob

    ) * 100

    # ======================================
    # RISK LEVEL
    # ======================================

    if risk_score < 25:

        risk_level = "Low"

    elif risk_score < 50:

        risk_level = "Moderate"

    elif risk_score < 75:

        risk_level = "High"

    else:

        risk_level = "Critical"

    # ======================================
    # ALERTS
    # ======================================

    alerts = []

    if hyp_prob > 0.7:

        alerts.append(
            "Potential Hypotension"
        )

    if tach_prob > 0.7:

        alerts.append(
            "Potential Tachycardia"
        )

    if spo2_prob > 0.7:

        alerts.append(
            "Potential Oxygen Desaturation"
        )

    # ======================================
    # DRIFT DETECTION
    # ======================================

    drift_report = detect_drift(

        reference_df,

        features_df
    )

    # ======================================
    # TELEMETRY LOGGING
    # ======================================

    log_path = os.path.join(

        BASE_DIR,

        "logs",

        "predictions.csv"
    )

    os.makedirs(

        os.path.dirname(log_path),

        exist_ok=True
    )

    log_row = pd.DataFrame([{

        "timestamp":
            datetime.now(),

        "hypotension_probability":
            hyp_prob,

        "tachycardia_probability":
            tach_prob,

        "low_spo2_probability":
            spo2_prob,

        "risk_score":
            risk_score,

        "risk_level":
            risk_level
    }])

    if not os.path.exists(log_path):

        log_row.to_csv(

            log_path,

            index=False
        )

    else:

        log_row.to_csv(

            log_path,

            mode="a",

            header=False,

            index=False
        )

    # ======================================
    # RESPONSE
    # ======================================

    return {

        "hypotension_probability":
            round(hyp_prob, 4),

        "tachycardia_probability":
            round(tach_prob, 4),

        "low_spo2_probability":
            round(spo2_prob, 4),

        "risk_score":
            round(risk_score, 2),

        "risk_level":
            risk_level,

        "alerts":
            alerts,

        "drift":
            drift_report
    }