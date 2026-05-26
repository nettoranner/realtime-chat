from fastapi import APIRouter, Depends

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import AsyncSessionLocal
from src.models.message import Message
from src.auth.dependencies import get_current_user


router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/{chat_id}")
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.id.asc())
    )

    messages = result.scalars().all()

    return [
        {
            "id": message.id,
            "chat_id": message.chat_id,
            "sender_id": message.sender_id,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]