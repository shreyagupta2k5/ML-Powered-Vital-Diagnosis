# test_websocket.py
import asyncio
import websockets
import httpx
import json

async def test_websocket_alert():
    patient_id = "WS_TEST_001"
    uri = f"ws://localhost:8000/ws/alerts/{patient_id}"
    
    print(f"Connecting to WebSocket: {uri}")
    async with websockets.connect(uri) as websocket:
        print("✅ Connected! Waiting for alerts...")
        
        # 1. Trigger a HIGH RISK prediction via HTTP
        payload = {
            "patient_id": patient_id,
            "track3_features": {
                "mean_hr": 150, "std_hr": 20, "min_hr": 120, "max_hr": 180,
                "mean_map": 50, "std_map": 5, "min_map": 40, "max_map": 60, "map_range": 20,
                "mean_spo2": 85, "std_spo2": 2, "min_spo2": 80,
                "mean_ecg": 1.0, "std_ecg": 0.5, "min_ecg": -0.5, "max_ecg": 2.5,
                "map_variability": 0.1, "hr_variability": 0.13, "ecg_range": 3.0, "map_drop": 10, "spo2_drop": 5
            }
        }
        
        print("🚀 Firing high-risk HTTP prediction...")
        asyncio.create_task(send_http_prediction(payload))
        
        # 2. Listen for the WebSocket alert
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"🔔 RECEIVED WEBSOCKET ALERT: {message}")
        except asyncio.TimeoutError:
            print("❌ Timeout: No alert received.")

async def send_http_prediction(payload):
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/api/v1/ensemble/predict", json=payload)

if __name__ == "__main__":
    asyncio.run(test_websocket_alert())