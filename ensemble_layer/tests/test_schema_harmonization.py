# ensemble_layer/tests/test_schema_harmonization.py
"""Test Schema Harmonization and 4-Tier Risk Scorer."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from ensemble_layer.services.aggregator import EnsembleAggregator
from ensemble_layer.services.risk_scorer import RiskTier

def test_critical_tier_and_harmonization():
    """Verify CRITICAL tier and feature harmonization."""
    aggregator = EnsembleAggregator()
    
    # Mock Track 1 (VitalDB) with HIGH SpO2 drop -> Should be CRITICAL
    mock_track1 = {
        "hypotension": {"probability": 0.10},
        "tachycardia": {"probability": 0.10},
        "oxygen_desaturation": {"probability": 0.95}, # High prob
        "top_shap_drivers": [
            {"feature": "mean_spo2", "shap_value": 0.4}, # Needs mapping to oxygen_saturation_mean
            {"feature": "std_hr", "shap_value": 0.2},
            {"feature": "map_range", "shap_value": 0.1}
        ]
    }
    mock_track2 = {"crisis_probability": 0.20}
    mock_track3 = {"mortality_probability": 0.20}

    result = aggregator.aggregate(mock_track1, mock_track2, mock_track3)

    print("=== SCHEMA HARMONIZATION TEST ===")
    print(f"Result: {result}")
    
    # Assertions
    assert result["risk_tier"] == "CRITICAL", f"Expected CRITICAL, got {result['risk_tier']}"
    assert "SpO2 Desaturation" in result["alert"], "Alert should mention dominant risk"
    
    # Check feature mapping (mean_spo2 -> oxygen_saturation_mean)
    assert "oxygen_saturation_mean" in result["top_features"], f"Features should be harmonized. Got: {result['top_features']}"
    assert len(result["top_features"]) <= 3, "Should have max 3 features"
    
    print("ALL SCHEMA TESTS PASSED")

if __name__ == "__main__":
    test_critical_tier_and_harmonization()