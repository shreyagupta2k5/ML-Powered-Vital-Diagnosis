# ==========================================
# TRACK 2 | ENSEMBLE PAYLOAD VALIDATION TESTS
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Verify that Track 2 inference output conforms to
#            the provisional Phase 7 ensemble JSON schema contract.
# ==========================================

import pytest
import json
import pathlib
import sys
from typing import Dict, List, Union

# Resolve project root for imports
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Provisional Phase 7 ensemble payload schema (subject to change)
ENSEMBLE_PAYLOAD_SCHEMA = {
    "type": "object",
    "required": [
        "track_id",
        "model_version",
        "crisis_probability",
        "severity_level",
        "crisis_type",
        "temporal_instability_score",
        "shap_top_drivers",
        "confidence_interval",
        "drift_status"
    ],
    "properties": {
        "track_id": {"type": "string", "enum": ["multi_morbidity_v1"]},
        "model_version": {"type": "string", "pattern": "^v\\d+\\.\\d+\\.\\d+$"},
        "crisis_probability": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "severity_level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH"]},
        "crisis_type": {"type": "string"},
        "temporal_instability_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "shap_top_drivers": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        "confidence_interval": {
            "type": "array",
            "items": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "minItems": 2,
            "maxItems": 2
        },
        "drift_status": {
            "type": "object",
            "required": ["psi_score", "ks_pvalue", "last_retrain"],
            "properties": {
                "psi_score": {"type": "number", "minimum": 0.0},
                "ks_pvalue": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "last_retrain": {"type": "string", "format": "date-time"}
            }
        }
    }
}

def validate_payload(payload: Dict) -> List[str]:
    """
    Validate a Track 2 inference response against the Phase 7 schema.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    
    # Check required fields
    for field in ENSEMBLE_PAYLOAD_SCHEMA["required"]:
        if field not in payload:
            errors.append(f"Missing required field: {field}")
    
    # Validate track_id
    if payload.get("track_id") not in ENSEMBLE_PAYLOAD_SCHEMA["properties"]["track_id"]["enum"]:
        errors.append(f"Invalid track_id: {payload.get('track_id')}")
    
    # Validate model_version format
    import re
    version_pattern = ENSEMBLE_PAYLOAD_SCHEMA["properties"]["model_version"]["pattern"]
    if not re.match(version_pattern, payload.get("model_version", "")):
        errors.append(f"Invalid model_version format: {payload.get('model_version')}")
    
    # Validate crisis_probability range
    proba = payload.get("crisis_probability")
    if not isinstance(proba, (int, float)) or not (0.0 <= proba <= 1.0):
        errors.append(f"crisis_probability out of range [0,1]: {proba}")
    
    # Validate severity_level
    if payload.get("severity_level") not in ENSEMBLE_PAYLOAD_SCHEMA["properties"]["severity_level"]["enum"]:
        errors.append(f"Invalid severity_level: {payload.get('severity_level')}")
    
    # Validate temporal_instability_score range
    instability = payload.get("temporal_instability_score")
    if not isinstance(instability, (int, float)) or not (0.0 <= instability <= 1.0):
        errors.append(f"temporal_instability_score out of range [0,1]: {instability}")
    
    # Validate shap_top_drivers
    drivers = payload.get("shap_top_drivers")
    if not isinstance(drivers, list) or not all(isinstance(d, str) for d in drivers):
        errors.append(f"shap_top_drivers must be array of strings: {drivers}")
    elif not (1 <= len(drivers) <= 5):
        errors.append(f"shap_top_drivers must have 1-5 items: {len(drivers)}")
    
    # Validate confidence_interval
    ci = payload.get("confidence_interval")
    if not isinstance(ci, list) or len(ci) != 2:
        errors.append(f"confidence_interval must be array of 2 numbers: {ci}")
    elif not all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in ci):
        errors.append(f"confidence_interval values out of range [0,1]: {ci}")
    elif ci[0] > ci[1]:
        errors.append(f"confidence_interval lower bound > upper bound: {ci}")
    
    # Validate drift_status
    drift = payload.get("drift_status")
    if not isinstance(drift, dict):
        errors.append(f"drift_status must be object: {drift}")
    else:
        for field in ["psi_score", "ks_pvalue", "last_retrain"]:
            if field not in drift:
                errors.append(f"drift_status missing required field: {field}")
        
        if "psi_score" in drift and (not isinstance(drift["psi_score"], (int, float)) or drift["psi_score"] < 0):
            errors.append(f"drift_status.psi_score must be non-negative number: {drift.get('psi_score')}")
        
        if "ks_pvalue" in drift and (not isinstance(drift["ks_pvalue"], (int, float)) or not (0.0 <= drift["ks_pvalue"] <= 1.0)):
            errors.append(f"drift_status.ks_pvalue must be in [0,1]: {drift.get('ks_pvalue')}")
        
        if "last_retrain" in drift:
            # Basic ISO 8601 date-time check
            import re
            iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
            if not re.match(iso_pattern, drift["last_retrain"]):
                errors.append(f"drift_status.last_retrain must be ISO 8601 date-time: {drift.get('last_retrain')}")
    
    return errors

class TestEnsemblePayload:
    """Test suite for Phase 7 ensemble payload validation."""
    
    def test_valid_payload(self):
        """Test that a well-formed Track 2 response passes validation."""
        valid_payload = {
            "track_id": "multi_morbidity_v1",
            "model_version": "v1.0.0",
            "crisis_probability": 0.007167879957705736,
            "severity_level": "LOW",
            "crisis_type": "none",
            "temporal_instability_score": 0.0,
            "shap_top_drivers": ["insulin_score", "glucose_std", "comorbidity_flag"],
            "confidence_interval": [0.0, 0.0871678814291954],
            "drift_status": {
                "psi_score": 0.0,
                "ks_pvalue": 1.0,
                "last_retrain": "2026-05-29T10:12:52.686216+00:00"
            }
        }
        errors = validate_payload(valid_payload)
        assert len(errors) == 0, f"Valid payload failed validation: {errors}"
    
    def test_missing_required_field(self):
        """Test that missing required fields are caught."""
        payload = {
            "track_id": "multi_morbidity_v1",
            "model_version": "v1.0.0",
            # Missing crisis_probability and other required fields
        }
        errors = validate_payload(payload)
        assert any("Missing required field: crisis_probability" in e for e in errors)
    
    def test_invalid_crisis_probability_range(self):
        """Test that out-of-range probability values are caught."""
        payload = self._get_valid_payload()
        payload["crisis_probability"] = 1.5
        errors = validate_payload(payload)
        assert any("crisis_probability out of range" in e for e in errors)
    
    def test_invalid_confidence_interval_order(self):
        """Test that lower > upper bound in CI is caught."""
        payload = self._get_valid_payload()
        payload["confidence_interval"] = [0.8, 0.2]  # Invalid order
        errors = validate_payload(payload)
        assert any("lower bound > upper bound" in e for e in errors)
    
    def test_invalid_severity_level(self):
        """Test that invalid severity levels are caught."""
        payload = self._get_valid_payload()
        payload["severity_level"] = "CRITICAL"  # Not in enum
        errors = validate_payload(payload)
        assert any("Invalid severity_level" in e for e in errors)
    
    def _get_valid_payload(self) -> Dict:
        """Helper to generate a valid base payload for testing."""
        return {
            "track_id": "multi_morbidity_v1",
            "model_version": "v1.0.0",
            "crisis_probability": 0.5,
            "severity_level": "MODERATE",
            "crisis_type": "isolated_glucose",
            "temporal_instability_score": 0.15,
            "shap_top_drivers": ["glucose_mean", "sbp_mean"],
            "confidence_interval": [0.42, 0.58],
            "drift_status": {
                "psi_score": 0.12,
                "ks_pvalue": 0.34,
                "last_retrain": "2026-05-29T10:00:00+00:00"
            }
        }

if __name__ == "__main__":
    pytest.main([__file__, "-v"])