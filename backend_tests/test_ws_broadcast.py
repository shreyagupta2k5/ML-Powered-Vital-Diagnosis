# backend_tests/test_ws_broadcast.py
import asyncio
import websockets
import json
import httpx

async def listen_for_alerts():
    uri = "ws://localhost:8000/ws/alerts/broadcast"
    print(f"Connecting to {uri}...")
    
    # Use a manual connect/disconnect approach for better control
    async with websockets.connect(uri) as websocket:
        print("✅ Connected! Waiting for alerts...")
        
        # Give the server a moment to register this connection in the 'global_alerts' set
        await asyncio.sleep(1.5) 
        
        # Now trigger the high-risk prediction
        payload = {
            "patient_id": "BROADCAST_TEST_FINAL",
            "track3_features": {
                "mean_hr": 150.0, "std_hr": 20.0, "min_hr": 120.0, "max_hr": 180.0,
                "mean_map": 50.0, "std_map": 5.0, "min_map": 40.0, "max_map": 60.0, "map_range": 20.0,
                "mean_spo2": 85.0, "std_spo2": 2.0, "min_spo2": 80.0,
                "mean_ecg": 1.0, "std_ecg": 0.5, "min_ecg": -0.5, "max_ecg": 2.5,
                "map_variability": 0.1, "hr_variability": 0.13, "ecg_range": 3.0, "map_drop": 10.0, "spo2_drop": 5.0
            }
        }
        
        print("🚀 Firing high-risk prediction...")
        async with httpx.AsyncClient() as client:
            await client.post("http://127.0.0.1:8000/api/v1/ensemble/predict", json=payload)
        
        # Wait for the message with a longer timeout
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=15)
            data = json.loads(message)
            print(f"🔔 ALERT RECEIVED: {json.dumps(data, indent=2)}")
            return True
        except asyncio.TimeoutError:
            print("❌ Timeout: No alert received within 15 seconds.")
            return False

if __name__ == "__main__":
    success = asyncio.run(listen_for_alerts())
    if success:
        print("\n✅ FIX 2 VERIFIED: Global Broadcast WebSocket is working!")
    else:
        print("\n❌ Fix 2 Failed: Check server logs and network.")