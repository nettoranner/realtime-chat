from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from src.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )
        
        return payload
    
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
    