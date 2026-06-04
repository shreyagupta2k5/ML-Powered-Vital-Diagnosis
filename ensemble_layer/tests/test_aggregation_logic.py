# ensemble_layer/tests/test_aggregation_logic.py
"""
Standalone test for Ensemble Aggregation Logic (Task 2.2 verification).
This tests the math and routing logic without needing live Track servers.
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from ensemble_layer.services.aggregator import EnsembleAggregator

def test_phase7_compliance():
    """Verify the aggregator produces Phase 7 compliant output."""
    aggregator = EnsembleAggregator()
    
    # Mock responses from Track 1, 2, and 3 APIs
    mock_track1 = {
        "hypotension": {"probability": 0.05},
        "tachycardia": {"probability": 0.10},
        "oxygen_desaturation": {"probability": 0.90} # High SpO2 drop
    }
    mock_track2 = {
        "crisis_probability": 0.40,
        "severity_label": "MODERATE"
    }
    mock_track3 = {
        "mortality_probability": 0.70,
        "risk_tier": "HIGH"
    }

    # Run aggregation
    result = aggregator.aggregate(mock_track1, mock_track2, mock_track3)

    # Assertions
    print("=== TESTING AGGREGATION LOGIC ===")
    print(f"Result: {result}")
    
    # 1. Risk Score Check (Weighted: T1*0.25 + T2*0.30 + T3*0.45)
    expected_score = (0.90 * 0.25) + (0.40 * 0.30) + (0.70 * 0.45)
    assert abs(result["risk_score"] - expected_score) < 0.01, "Risk score calculation mismatch"
    
    # 2. Tier Check (Score > 0.60 should be HIGH)
    assert result["risk_tier"] == "HIGH", f"Risk tier mismatch: got {result['risk_tier']}"
    
    # 3. Alert Generation
    assert "CRITICAL" in result["alert"], "Alert generation failed"
    
    # 4. Feature Extraction
    assert len(result["top_features"]) > 0, "Top features list is empty"

    print("ALL LOGIC TESTS PASSED")
    return True

if __name__ == "__main__":
    test_phase7_compliance()