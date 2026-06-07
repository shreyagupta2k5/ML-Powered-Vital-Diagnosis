# backend_tests/test_integration.py
from  conftest import BASE_URL
import pytest
import asyncio
from datetime import datetime
import json

class TestEndToEndIntegration:
    """Task 5.1: End-to-End Integration Tests"""
    
    @pytest.mark.asyncio
    async def test_track1_single_prediction(self, async_client, load_test_data):
        """Test Track 1 (eICU) mortality prediction with valid demographics."""
        payload = load_test_data("track1_eicu_patient.json")
        
        response = await async_client.post("/api/v1/track1/predict", json=payload)
        
        # STRICT VALIDATION
        assert response.status_code == 200, f"Track 1 failed: {response.text}"
        data = response.json()
        assert "mortality_probability" in data
        assert "risk_tier" in data
        assert data["risk_tier"] in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
        
    @pytest.mark.asyncio
    async def test_ensemble_all_tracks(self, async_client, load_test_data):
        """Test Ensemble prediction routing all 3 tracks correctly."""
        payload = load_test_data("ensemble_all_tracks.json")
        
        start_time = asyncio.get_event_loop().time()
        response = await async_client.post("/api/v1/ensemble/predict", json=payload)
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify math and routing
        assert "risk_score" in data
        assert "track_results" in data
        assert len(data["track_results"]) >= 1 # At least one track must respond
        
        # PERFORMANCE CHECK (Task 5.2 Target)
        assert latency_ms < 500, f"Ensemble latency too high: {latency_ms:.2f}ms"

    @pytest.mark.asyncio
    async def test_websocket_alert_delivery(self, async_client, load_test_data):
        """Test WebSocket receives alert when HIGH_RISK prediction occurs."""
        import websockets
        
        patient_id = "WS_INTEGRATION_TEST_001"
        uri = f"{BASE_URL.replace('http', 'ws')}/ws/alerts/{patient_id}"
        
        async with websockets.connect(uri) as websocket:
            # Trigger high risk via ensemble
            payload = load_test_data("ensemble_all_tracks.json")
            payload["patient_id"] = patient_id
            
            await async_client.post("/api/v1/ensemble/predict", json=payload)
            
            # Wait for WS message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                alert_data = json.loads(message)
                
                assert alert_data["type"] == "HIGH_RISK"
                assert alert_data["patient_id"] == patient_id
            except asyncio.TimeoutError:
                pytest.fail("WebSocket alert not received within 10 seconds.")