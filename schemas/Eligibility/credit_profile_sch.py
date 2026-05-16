from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class CreditProfileBase(BaseModel):
    pan_number: str = Field(..., min_length=10, max_length=10)
    credit_score: Optional[int]
    credit_band: Optional[str]
    credit_status: Optional[str]
    bureau_name: str
    enquiry_type: str


class CreditProfileCreate(CreditProfileBase):
    user_id: int
    score_generated_at: Optional[datetime]
    raw_bureau_response: Optional[Dict]


class CreditProfileResponse(CreditProfileBase):
    id: int
    user_id: int
    fetched_at: datetime

    class Config:
        from_attributes = True
