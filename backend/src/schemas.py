from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


class MessageResponse(BaseModel):
    sender: str
    text: str
    is_system: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomBase(BaseModel):
    name: str


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: int
    is_group: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)