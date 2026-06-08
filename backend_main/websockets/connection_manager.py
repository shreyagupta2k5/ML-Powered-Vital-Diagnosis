# backend_main/websockets/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.groups: Dict[str, Set[WebSocket]] = {} 

    async def connect(self, websocket: WebSocket, patient_id: str):
        await websocket.accept()
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = []
        self.active_connections[patient_id].append(websocket)
        logger.info(f"Client connected to patient channel: {patient_id}")

    def disconnect(self, websocket: WebSocket, patient_id: str):
        if patient_id in self.active_connections:
            self.active_connections[patient_id].remove(websocket)
            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]

    async def connect_to_group(self, websocket: WebSocket, group_name: str):
        """Connect a websocket to a named broadcast group."""
        await websocket.accept()
        if group_name not in self.groups:
            self.groups[group_name] = set()
        
        # Ensure we don't add duplicates
        self.groups[group_name].add(websocket)
        logger.info(f"✅ Client joined group '{group_name}'. Total members: {len(self.groups[group_name])}")

    def disconnect_from_group(self, websocket: WebSocket, group_name: str):
        if group_name in self.groups:
            self.groups[group_name].discard(websocket)
            logger.info(f"❌ Client left group '{group_name}'. Remaining members: {len(self.groups[group_name])}")
            if not self.groups[group_name]:
                del self.groups[group_name]

    async def send_personal_message(self, message: dict, patient_id: str):
        if patient_id in self.active_connections:
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to patient {patient_id}: {e}")

    async def broadcast_to_group(self, group_name: str, message: dict):
        """Send a message to all members of a specific group."""
        if group_name in self.groups:
            logger.info(f"📡 Attempting to broadcast to {len(self.groups[group_name])} members in '{group_name}'")
            disconnected = set()
            for connection in self.groups[group_name]:
                try:
                    await connection.send_json(message)
                    logger.info("✅ Message sent successfully to one member")
                except Exception as e:
                    logger.error(f"Error broadcasting to group member: {e}")
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.groups[group_name].discard(conn)
            if not self.groups[group_name]:
                del self.groups[group_name]
        else:
            logger.warning(f"⚠️ Group '{group_name}' does not exist or is empty!")

    async def broadcast(self, message: dict):
        for patient_connections in self.active_connections.values():
            for connection in patient_connections:
                await connection.send_json(message)
        for group in self.groups.values():
            for connection in group:
                await connection.send_json(message)

manager = ConnectionManager()