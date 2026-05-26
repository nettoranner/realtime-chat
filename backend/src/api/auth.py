from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.database import AsyncSessionLocal
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin
from src.auth.hashing import Hash
from src.auth.jwt import create_access_token


router = APIRouter(prefix="/auth")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists",
        )
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=Hash.hash_password(
            user_data.password
        ),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "message": "User created",
    }

@router.post("/login")
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    
    if not Hash.verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
    
    token = create_access_token(
        {
            "sub": str(user.id)
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }