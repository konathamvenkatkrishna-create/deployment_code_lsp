# app/schemas/loan_timeline_schema.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LoanStatusHistoryItem(BaseModel):
    id: int
    old_status: Optional[str]
    new_status: str
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LoanTimelineResponse(BaseModel):
    application_id: int
    timeline: List[LoanStatusHistoryItem]