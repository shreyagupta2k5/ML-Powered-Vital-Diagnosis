# test_error_handling.py
import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_malformed_payload():
    """Test that malformed JSON triggers graceful degradation (502), not server crash (500)."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        payload = {
            "patient_id": "ERR_TEST_001",
            "track2_features": {
                "glucose_mean": "not_a_number", 
                "glucose_count": 5,
                "sbp_mean": 118,
                "sbp_count": 4,
                "map_mean": 75,
                "map_count": 3
            }
        }
        response = await client.post("/api/v1/ensemble/predict", json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Because of graceful degradation, we expect a 502 Bad Gateway 
        # indicating Track 2 failed, rather than a 500 Internal Server Error.
        if response.status_code == 502:
            print("✅ PASS: Malformed payload correctly handled via graceful degradation (502).")
        elif response.status_code == 422:
            print("⚠️ PARTIAL: Payload rejected at gateway level (422). Graceful degradation not triggered.")
        else:
            print(f"❌ FAIL: Unexpected status code {response.status_code}. Expected 502 or 422.")

if __name__ == "__main__":
    asyncio.run(test_malformed_payload())