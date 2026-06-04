# ensemble_layer/tests/test_aggregator.py
"""Unit tests for EnsembleAggregator."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from ensemble_layer.services.aggregator import EnsembleAggregator

def test_aggregate():
    """Test ensemble aggregation with sample inputs."""
    aggregator = EnsembleAggregator()
    
    # Mock track outputs
    track1 = {
        "hypotension": {"probability": 0.04},
        "tachycardia": {"probability": 0.12},
        "oxygen_desaturation": {"probability": 0.87}
    }
    track2 = {"crisis_probability": 0.31, "severity_label": "MODERATE"}
    track3 = {"mortality_probability": 0.67, "risk_tier": "HIGH"}
    
    result = aggregator.aggregate(track1, track2, track3)
    
    print("=== AGGREGATOR TEST ===")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Tier: {result['risk_tier']}")
    print(f"Track Scores: {result['track_scores']}")
    print(f"Alert: {result['alert']}")
    print(f"Top Features: {result['top_features']}")
    
    # Assertions
    assert 0.0 <= result['risk_score'] <= 1.0
    assert result['risk_tier'] in ["HIGH", "MODERATE", "LOW"]
    assert "spo2_mean" in result['top_features']  # Track 1 high SpO2 drop
    assert "lactate_mean" in result['top_features']  # Track 3 high mortality
    print("All assertions passed")

if __name__ == "__main__":
    test_aggregate()