from pydantic import BaseModel

from datetime import datetime


class ComplaintReplyCreate(BaseModel):

    message: str


class ComplaintReplyResponse(BaseModel):

    id: int

    complaint_id: int

    sender_type: str

    sender_id: int

    message: str

    created_at: datetime

    class Config:
        from_attributes = True