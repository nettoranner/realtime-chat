from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models import User, Message, ChatRoom
from src.schemas import UserCreate, RoomCreate
from src.auth import get_password_hash

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_schema: UserCreate) -> User:
    hashed_pw = get_password_hash(user_schema.password)
    db_user = User(
        username=user_schema.username,
        hashed_password=hashed_pw
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def create_room_message(db: AsyncSession, text: str, sender_id: int, room_id: int) -> Message:
    db_message = Message(
        text=text,
        sender_id=sender_id,
        chat_room_id=room_id
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_room_messages(db: AsyncSession, room_id: int, limit: int = 50) -> list[Message]:
    query = (
        select(Message)
        .where(Message.chat_room_id == room_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_all_rooms(db: AsyncSession) -> list[ChatRoom]:
    query = select(ChatRoom).order_by(ChatRoom.id.asc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def create_chat_room(db: AsyncSession, room_schema: RoomCreate) -> ChatRoom:
    db_room = ChatRoom(
        name=room_schema.name,
        is_group=True
    )
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    return db_room

async def seed_rooms(db: AsyncSession):
    """Automatically seed default rooms and reset PostgreSQL ID sequence"""
    default_rooms = [
        (1, 'General'),
        (2, 'Random'),
        (3, 'Support')
    ]
    for r_id, r_name in default_rooms:
        query = select(ChatRoom).where(ChatRoom.id == r_id)
        result = await db.execute(query)
        room = result.scalar_one_or_none()
        
        if not room:
            db.add(ChatRoom(id=r_id, name=r_name, is_group=True))
            print(f"Room '{r_name}' successfully created in DB")
            
    await db.commit()

    # Reset PostgreSQL sequence to prevent UniqueViolationError on custom room creations
    await db.execute(
        text("SELECT setval(pg_get_serial_sequence('chat_rooms', 'id'), coalesce(max(id), 1)) FROM chat_rooms;")
    )
    await db.commit()