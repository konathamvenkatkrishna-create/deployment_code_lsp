from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    application_id: Optional[int]
    title: str
    message: str
    type: str                 # STATUS_UPDATE / DOCUMENT / NBFC
    channel: str              # IN_APP / SMS
    status: str               # SENT / FAILED
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True