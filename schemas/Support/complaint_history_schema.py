from pydantic import BaseModel
from datetime import datetime


class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    old_status: str | None = None
    new_status: str
    comment: str | None = None
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True