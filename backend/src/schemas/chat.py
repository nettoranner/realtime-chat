from pydantic import BaseModel


class ChatCreate(BaseModel):
    name: str


class ChatResponse(BaseModel):
    id: int
    name: str
