"""
schemas.py — Pydantic models for Track 1 eICU Mortality Prediction API
Author: Shreya Gupta
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST
# ─────────────────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    """
    Input payload for POST /api/v1/track1/predict.

    Accepts either:
      (a) a flat dict of pre-aggregated features (562 columns), or
      (b) the same keys as top-level fields via model_validate().

    All 562 feature columns from metadata/feature_columns.csv are accepted.
    Only the fields listed below are *required*; the rest are optional and
    will be imputed to 0.0 by the pipeline if missing.
    """

    # ── Required demographic / stay features ────────────────────────────────
    age: float = Field(..., description="Patient age in years", ge=0, le=130)
    gender: Literal["Male", "Female", "Unknown", "Other"] = Field(
        ..., description="Patient gender"
    )
    ethnicity: Optional[str] = Field(
        None,
        description=(
            "Ethnicity label — one of: African American, Asian, Caucasian, "
            "Hispanic, Native American, Other/Unknown"
        ),
    )
    admissionweight: Optional[float] = Field(
        None, description="Admission body weight (kg)", ge=0, le=400
    )

    # ── Vital-sign aggregates (mean / min / max / std / count) ───────────────
    heartrate_mean: Optional[float] = Field(None, ge=0, le=350)
    heartrate_min: Optional[float] = Field(None, ge=0, le=350)
    heartrate_max: Optional[float] = Field(None, ge=0, le=350)
    heartrate_std: Optional[float] = Field(None, ge=0)
    heartrate_count: Optional[float] = Field(None, ge=0)

    respiration_mean: Optional[float] = Field(None, ge=0, le=100)
    respiration_min: Optional[float] = Field(None, ge=0, le=100)
    respiration_max: Optional[float] = Field(None, ge=0, le=100)
    respiration_std: Optional[float] = Field(None, ge=0)
    respiration_count: Optional[float] = Field(None, ge=0)

    sao2_mean: Optional[float] = Field(None, ge=0, le=100)
    sao2_min: Optional[float] = Field(None, ge=0, le=100)
    sao2_max: Optional[float] = Field(None, ge=0, le=100)
    sao2_std: Optional[float] = Field(None, ge=0)
    sao2_count: Optional[float] = Field(None, ge=0)

    temperature_mean: Optional[float] = Field(None, ge=25, le=45)
    temperature_min: Optional[float] = Field(None, ge=25, le=45)
    temperature_max: Optional[float] = Field(None, ge=25, le=45)
    temperature_std: Optional[float] = Field(None, ge=0)
    temperature_count: Optional[float] = Field(None, ge=0)

    systemicsystolic_mean: Optional[float] = Field(None, ge=0, le=300)
    systemicsystolic_min: Optional[float] = Field(None, ge=0, le=300)
    systemicsystolic_max: Optional[float] = Field(None, ge=0, le=300)
    systemicsystolic_std: Optional[float] = Field(None, ge=0)

    systemicdiastolic_mean: Optional[float] = Field(None, ge=0, le=200)
    systemicdiastolic_min: Optional[float] = Field(None, ge=0, le=200)
    systemicdiastolic_max: Optional[float] = Field(None, ge=0, le=200)
    systemicdiastolic_std: Optional[float] = Field(None, ge=0)

    systemicmean_mean: Optional[float] = Field(None, ge=0, le=250)
    systemicmean_min: Optional[float] = Field(None, ge=0, le=250)
    systemicmean_max: Optional[float] = Field(None, ge=0, le=250)
    systemicmean_std: Optional[float] = Field(None, ge=0)

    # ── Key lab aggregates ────────────────────────────────────────────────────
    lactate_mean: Optional[float] = Field(None, ge=0)
    lactate_min: Optional[float] = Field(None, ge=0)
    lactate_max: Optional[float] = Field(None, ge=0)
    lactate_std: Optional[float] = Field(None, ge=0)

    creatinine_mean: Optional[float] = Field(None, ge=0)
    creatinine_min: Optional[float] = Field(None, ge=0)
    creatinine_max: Optional[float] = Field(None, ge=0)

    glucose_mean: Optional[float] = Field(None, ge=0)
    glucose_min: Optional[float] = Field(None, ge=0)
    glucose_max: Optional[float] = Field(None, ge=0)

    # ── Remaining 500+ features passed as a free-form dict ───────────────────
    extra_features: Optional[Dict[str, Optional[float]]] = Field(
        default=None,
        description=(
            "Any remaining feature columns from feature_columns.csv not "
            "listed above. Keys must match column names exactly."
        ),
    )

    # ── Optional metadata (never used in model, only for logging) ────────────
    patient_id: Optional[str] = Field(
        None, description="Caller-supplied patient identifier for audit log"
    )
    observation_window_hours: Optional[Literal[6, 12, 24]] = Field(
        24,
        description="Observation window used to aggregate features (default 24h)",
    )

    model_config = {"extra": "allow"}  # absorb unknown columns silently

    @model_validator(mode="before")
    @classmethod
    def flatten_extra(cls, values: dict) -> dict:
        """
        If the caller sends the full 562-column flat dict (no nesting),
        pass it straight through — Pydantic will populate declared fields
        and silently ignore the rest (extra='allow').
        """
        return values


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

class SHAPDriver(BaseModel):
    feature: str = Field(..., description="Feature name")
    shap_value: float = Field(..., description="SHAP contribution (signed)")
    direction: Literal["increases_risk", "decreases_risk"] = Field(
        ..., description="Direction of impact on mortality probability"
    )


class PredictResponse(BaseModel):
    """Full prediction response returned by POST /api/v1/track1/predict."""

    patient_id: Optional[str] = Field(None, description="Echo of input patient_id")
    mortality_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Predicted ICU mortality probability (0–1)",
    )
    risk_tier: Literal["HIGH", "MODERATE", "LOW"] = Field(
        ...,
        description=(
            "Clinical risk tier derived from probability:\n"
            "  HIGH     ≥ 0.30\n"
            "  MODERATE 0.15 – 0.30\n"
            "  LOW      < 0.15"
        ),
    )
    recommended_action: str = Field(
        ..., description="Clinical action guidance based on risk tier"
    )
    top_shap_drivers: List[SHAPDriver] = Field(
        default_factory=list,
        description="Top-5 SHAP feature contributions for this prediction",
    )
    model_version: str = Field(..., description="Model identifier used")
    observation_window_hours: int = Field(
        ..., description="Observation window the input features cover"
    )
    alert_threshold_used: float = Field(
        ..., description="Decision threshold applied to produce risk_tier"
    )


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]
    model_loaded: bool
    model_version: str
    feature_count: int
    message: str