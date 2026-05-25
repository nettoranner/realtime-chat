from jose import jwt,JWTError

from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect

from sqlalchemy.ext.asyncio import AsyncSession

from src.websocket.manager import manager
from src.database.database import AsyncSessionLocal
from src.models.message import Message
from src.core.config import settings


router = APIRouter()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_from_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except JWTError:
        return None


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION
        )
        return

    user_id = await get_user_from_token(token)

    if not user_id:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION
        )
        return

    await manager.connect(chat_id, websocket)

    async with AsyncSessionLocal() as db:

        try:
            while True:
                data = await websocket.receive_json()

                content = data.get("content")

                if not content:
                    continue

                content = content.strip()

                if len(content) == 0:
                    continue

                if len(content) > 2000:
                    continue

                message = Message(
                    chat_id=chat_id,
                    sender_id=user_id,
                    content=content,
                )

                db.add(message)

                await db.commit()

                await db.refresh(message)

                response_data = {
                    "id": message.id,
                    "chat_id": message.chat_id,
                    "sender_id": message.sender_id,
                    "content": message.content,
                }

                await manager.broadcast(
                    chat_id,
                    response_data,
                )

        except WebSocketDisconnect:
            manager.disconnect(
                chat_id,
                websocket,
            )

            await manager.broadcast(
                chat_id,
                {
                    "system": True,
                    "message": f"User {user_id} disconnected"
                },
            )

        except Exception as e:
            manager.disconnect(
                chat_id,
                websocket,
            )

            print("WebSocket error:", e)

            await websocket.close()