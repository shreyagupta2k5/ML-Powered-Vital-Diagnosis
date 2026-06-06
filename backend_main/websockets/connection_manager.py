from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections = {}

    async def connect(
        self,
        websocket: WebSocket,
        patient_id: str
    ):

        await websocket.accept()

        if patient_id not in self.active_connections:

            self.active_connections[patient_id] = []

        self.active_connections[
            patient_id
        ].append(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        patient_id: str
    ):

        if patient_id in self.active_connections:

            self.active_connections[
                patient_id
            ].remove(websocket)

            if not self.active_connections[
                patient_id
            ]:

                del self.active_connections[
                    patient_id
                ]

    async def send_personal_message(
        self,
        message: dict,
        patient_id: str
    ):

        if patient_id in self.active_connections:

            for connection in self.active_connections[
                patient_id
            ]:

                await connection.send_json(
                    message
                )

    async def broadcast(
        self,
        message: dict
    ):

        for patient_connections in (
            self.active_connections.values()
        ):

            for connection in patient_connections:

                await connection.send_json(
                    message
                )


manager = ConnectionManager()