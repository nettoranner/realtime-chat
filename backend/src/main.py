import jwt
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, async_session_maker
from src.config import settings
from src.schemas import UserCreate, UserResponse, Token, MessageResponse, RoomCreate, RoomResponse
from src.crud import (
    get_user_by_username, 
    create_user, 
    create_room_message, 
    get_room_messages, 
    seed_rooms,
    get_all_rooms,      
    create_chat_room    
)
from src.auth import verify_password, create_access_token
from src.websocket_manager import manager
from src.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_maker() as session:
        await seed_rooms(session)
    yield

app = FastAPI(title="RTChat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


# --- Auth Endpoints ---

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    return await create_user(db, user_data)


@app.post("/auth/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Successfully logged out"}


# --- Rooms management ---

@app.get("/rooms", response_model=list[RoomResponse])
async def get_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_all_rooms(db)


@app.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_chat_room(db, room_data)


# --- Message history ---

@app.get("/rooms/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages_history(
    room_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    db_messages = await get_room_messages(db, room_id=room_id)
    formatted_messages = [
        MessageResponse(
            sender=msg.sender.username,
            text=msg.text,
            is_system=False,
            created_at=msg.created_at
        ) for msg in db_messages
    ]
    return formatted_messages


# --- WebSocket ---

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    db: AsyncSession = Depends(get_db)
):
    token = websocket.cookies.get("access_token")
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = await get_user_by_username(db, username=username)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id)
    
    join_notification = {
        "sender": "System",
        "text": f"User {user.username} joined the chat",
        "is_system": True
    }
    await manager.broadcast(join_notification, room_id)

    try:
        while True:
            data = await websocket.receive_json()
            text_content = data.get("text", "").strip()
            
            if not text_content:
                continue
            
            async with async_session_maker() as session:
                await create_room_message(
                    db=session,
                    text=text_content,
                    sender_id=user.id,
                    room_id=room_id
                )
            
            message_to_send = {
                "sender": user.username,
                "text": text_content,
                "is_system": False
            }
            await manager.broadcast(message_to_send, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        leave_notification = {
            "sender": "System",
            "text": f"User {user.username} left the chat",
            "is_system": True
        }
        await manager.broadcast(leave_notification, room_id)