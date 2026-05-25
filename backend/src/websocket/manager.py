from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(dict)

    async def connect(
        self,
        chat_id: int,
        user_id: int,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_connections[chat_id][
            user_id
        ] = websocket

    def disconnect(
        self,
        chat_id: int,
        user_id: int,
    ):
        if (
            chat_id in self.active_connections
            and user_id in self.active_connections[chat_id]
        ):
            del self.active_connections[chat_id][
                user_id
            ]

            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def send_personal_message(
        self,
        websocket: WebSocket,
        message: dict,
    ):
        await websocket.send_json(message)

    async def broadcast(
        self,
        chat_id: int,
        message: dict,
    ):
        if chat_id not in self.active_connections:
            return

        disconnected_users = []

        for (
            user_id,
            connection,
        ) in self.active_connections[
            chat_id
        ].items():

            try:
                await connection.send_json(message)

            except Exception:
                disconnected_users.append(user_id)

        for user_id in disconnected_users:
            self.disconnect(chat_id, user_id)

    def get_online_users(
        self,
        chat_id: int,
    ):
        if chat_id not in self.active_connections:
            return []

        return list(
            self.active_connections[chat_id].keys()
        )


manager = ConnectionManager()