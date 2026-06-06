# ensemble_layer/api/schemas.py
"""
Pydantic schemas for Ensemble API request/response validation.
Centralized schema definitions for consistency.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

# class Track1SignalInput(BaseModel):
#     """Raw waveform input for Track 1."""
#     ecg: List[float] = Field(..., description="ECG waveform samples")
#     hr: List[float] = Field(..., description="Heart rate time series")
#     map: List[float] = Field(..., description="Mean arterial pressure time series")
#     spo2: List[float] = Field(..., description="Oxygen saturation time series")

class Track3SignalInput(BaseModel):
    """Raw waveform input for Track 3 (VitalDB)."""
    ecg: List[float] = Field(..., description="ECG waveform samples")
    hr: List[float] = Field(..., description="Heart rate time series")
    map: List[float] = Field(..., description="Mean arterial pressure time series")
    spo2: List[float] = Field(..., description="Oxygen saturation time series")

# class Track1FeatureInput(BaseModel):
class Track3FeatureInput(BaseModel):
    """Pre-extracted features for Track 1."""
    mean_hr: float
    std_hr: float
    min_hr: float
    max_hr: float
    mean_map: float
    std_map: float
    min_map: float
    max_map: float
    map_range: float
    mean_spo2: float
    std_spo2: float
    min_spo2: float
    mean_ecg: float
    std_ecg: float
    min_ecg: float
    max_ecg: float
    map_variability: float
    hr_variability: float
    ecg_range: float
    map_drop: float
    spo2_drop: float

class EnsembleInput(BaseModel):
    """Unified input schema for ensemble prediction."""
    patient_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    # # Track-specific inputs
    # track1_signals: Optional[Track1SignalInput] = None
    # track1_features: Optional[Track1FeatureInput] = None
    # track2_features: Optional[Dict[str, float]] = None
    # track3_features: Optional[Dict[str, float]] = None
    
    # Track 1: eICU (Accepts Any because it requires string demographics)
    track1_features: Optional[Dict[str, Any]] = None 
    # Track 2: MIMIC
    track2_features: Optional[Dict[str, float]] = None
    # Track 3: VitalDB
    track3_signals: Optional[Track3SignalInput] = None
    track3_features: Optional[Track3FeatureInput] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "PT_001",
                "track2_features": {
                    "glucose_mean": 145.0,
                    "glucose_count": 10.0,
                    "sbp_mean": 135.0,
                    "sbp_count": 50.0,
                    "map_mean": 95.0,
                    "map_count": 50.0
                }
            }
        }