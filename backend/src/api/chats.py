from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from src.database.database import AsyncSessionLocal
from src.models.chat import Chat
from src.schemas.chat import ChatCreate
from src.auth.dependencies import get_current_user
from src.models.member import ChatMember



router = APIRouter(prefix="/chats")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("")
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    chat = Chat(name=data.name)

    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    member = ChatMember(
        chat_id=chat.id,
        user_id=user.id,
    )

    db.add(member)
    await db.commit()

    return {
        "id": chat.id,
        "name": chat.name,
    }


@router.get("")
async def get_chats(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(select(Chat))

    chats = result.scalars().all()
    
    return chats