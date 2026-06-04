"""
early_warning_system.py
Risk stratification and clinical alert generation.
"""
import numpy as np
import pandas as pd


def generate_early_warning(
    patient_id: int,
    risk_score: float,
    shap_values: np.ndarray,
    feature_names: list,
    vitals_row: pd.Series,
    threshold_high: float = 0.30,
    threshold_medium: float = 0.15,
) -> dict:
    """
    Convert risk score + SHAP values into a structured clinical alert.
    Returns a dict with alert_level, top_drivers, vital_flags,
    and recommendation.
    """
    alert = {
        "patient_id":     patient_id,
        "risk_score":     round(float(risk_score), 4),
        "alert_level":    None,
        "top_drivers":    [],
        "vital_flags":    [],
        "recommendation": "",
    }

    if risk_score >= threshold_high:
        alert["alert_level"] = "RED — Immediate Review"
    elif risk_score >= threshold_medium:
        alert["alert_level"] = "AMBER — Monitor Closely"
    else:
        alert["alert_level"] = "GREEN — Stable"

    shap_series = pd.Series(shap_values, index=feature_names)
    top3 = shap_series.abs().nlargest(3)
    alert["top_drivers"] = [
        f"{feat} (impact={shap_series[feat]:+.3f})"
        for feat in top3.index
    ]

    clinical_limits = {
        "heartrate_mean":   (50,  120,  "Heart Rate"),
        "sao2_mean":        (90,  100,  "SpO2"),
        "respiration_mean": (8,   25,   "Resp Rate"),
        "temperature_mean": (35,  38.5, "Temperature"),
        "systemicmean_mean":(60,  100,  "MAP"),
    }
    for col, (lo, hi, label) in clinical_limits.items():
        if col in vitals_row.index:
            val = vitals_row[col]
            if not np.isnan(val) and (val < lo or val > hi):
                alert["vital_flags"].append(
                    f"{label}={val:.1f} [normal {lo}–{hi}]"
                )

    if alert["alert_level"].startswith("RED"):
        alert["recommendation"] = (
            "Escalate to attending physician immediately. "
            "Consider ICU-level intervention."
        )
    elif alert["alert_level"].startswith("AMBER"):
        alert["recommendation"] = (
            "Increase monitoring frequency. "
            "Review top risk drivers with care team."
        )
    else:
        alert["recommendation"] = "Continue routine monitoring."

    return alert


def batch_stratify(
    patient_ids: np.ndarray,
    probabilities: np.ndarray,
    actual_labels: np.ndarray = None,
    threshold_high: float = 0.30,
    threshold_medium: float = 0.15,
) -> pd.DataFrame:
    """
    Produce a risk-stratified table for a batch of patients.
    """
    def tier(p):
        if p >= threshold_high:   return "HIGH"
        if p >= threshold_medium: return "MODERATE"
        return "LOW"

    df = pd.DataFrame({
        "Patient_ID":     patient_ids,
        "Mortality_Risk": probabilities.round(4),
        "Risk_Tier":      [tier(p) for p in probabilities],
    })
    if actual_labels is not None:
        df["Actual_Mortality"] = actual_labels
    return df.sort_values("Mortality_Risk", ascending=False).reset_index(drop=True)
