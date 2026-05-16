from pydantic import BaseModel
from datetime import datetime


class ChatCreate(BaseModel):
    message: str


class ChatResponse(BaseModel):
    id: int
    user_id: int
    sender: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True