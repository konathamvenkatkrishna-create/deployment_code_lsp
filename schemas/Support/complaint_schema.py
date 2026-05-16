from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from core.enums import ComplaintStatusEnum, ComplaintPriority, ComplaintCategory


class ComplaintCreate(BaseModel):
    application_id: Optional[int] = None
    category: ComplaintCategory
    subject: str
    description: str
    priority: ComplaintPriority = ComplaintPriority.MEDIUM
    attachment_url: Optional[str] = None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatusEnum
    comment: Optional[str] = None


class ComplaintHistoryResponse(BaseModel):
    id: int
    complaint_id: int
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    user_id: int
    application_id: Optional[int] = None
    category: ComplaintCategory
    subject: str
    description: str
    priority: ComplaintPriority
    status: ComplaintStatusEnum
    attachment_url: Optional[str] = None
    escalated: bool = False
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintDetailResponse(ComplaintResponse):
    history: List[ComplaintHistoryResponse] = []

    class Config:
        from_attributes = True