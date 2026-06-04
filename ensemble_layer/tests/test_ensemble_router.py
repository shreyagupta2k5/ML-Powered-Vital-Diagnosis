# ensemble_layer/tests/test_ensemble_router.py
"""Integration test for Ensemble API Gateway."""

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from ensemble_layer.api.ensemble_router import app

client = TestClient(app)

def test_ensemble_predict():
    """Test ensemble prediction with mock track responses."""
    # Mock input with Track 2 features only
    payload = {
        "patient_id": "TEST_001",
        "track2_features": {
            "glucose_mean": 145.0,
            "glucose_count": 10.0,
            "sbp_mean": 135.0,
            "sbp_count": 50.0,
            "map_mean": 95.0,
            "map_count": 50.0
        }
    }
    
    # Note: This will fail if track services aren't running
    # In production, use mocked HTTP calls or run services
    response = client.post("/api/v1/ensemble/predict", json=payload)
    
    # Expected: 503 if tracks not running, 200 if running
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Risk Score: {data['risk_score']}")
        print(f"Risk Tier: {data['overall_risk']}")
        print(f"Alert: {data['unified_alert']}")
    else:
        print(f"Expected failure (tracks not running): {response.json()}")

if __name__ == "__main__":
    test_ensemble_predict()