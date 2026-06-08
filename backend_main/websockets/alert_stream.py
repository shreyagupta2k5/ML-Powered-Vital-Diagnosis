# backend_main/websockets/alert_stream.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend_main.websockets.connection_manager import manager

router = APIRouter()

# =====================================
# MESSAGE BUFFER
# =====================================
alert_queue = asyncio.Queue()

# =====================================
# BACKGROUND WORKER
# =====================================
async def alert_worker():
    while True:
        patient_id, message = await alert_queue.get()
        try:
            # 1. Send to specific patient
            await manager.send_personal_message(message, patient_id)
            
            # 2. Send to Global Broadcast channel for Dashboard Bell
            print(f"📡 Broadcasting alert to global_alerts group: {message}")
            await manager.broadcast_to_group("global_alerts", message)
            
        except Exception as e:
            print(f"Alert delivery failed: {e}")
        finally:
            alert_queue.task_done()

# =====================================
# START WORKER ON APP STARTUP
# =====================================
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(alert_worker())

# =====================================
# WEBSOCKET ENDPOINTS
# =====================================

# ⚠️ CRITICAL FIX: Specific route MUST come before the generic {patient_id} route
@router.websocket("/ws/alerts/broadcast")
async def broadcast_endpoint(websocket: WebSocket):
    """Endpoint for Dashboard Bell to listen to all high-risk alerts."""
    await manager.connect_to_group(websocket, "global_alerts")
    print(f"✅ New client connected to global_alerts group")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_from_group(websocket, "global_alerts")
        print(f"❌ Client disconnected from global_alerts group")

@router.websocket("/ws/alerts/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: str):
    await manager.connect(websocket, patient_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, patient_id)

# =====================================
# ALERT PUBLISHER
# =====================================
async def publish_alert(patient_id: str, message: dict):
    await alert_queue.put((patient_id, message))

async def publish_high_risk(patient_id: str, risk_score: float):
    await publish_alert(
        patient_id,
        {
            "type": "HIGH_RISK",
            "patient_id": patient_id,
            "risk_score": risk_score
        }
    )

async def publish_drift(feature_name: str):
    await manager.broadcast({
        "type": "DRIFT_DETECTED",
        "feature": feature_name
    })

async def publish_model_update(version: str):
    await manager.broadcast({
        "type": "MODEL_UPDATED",
        "version": version
    })