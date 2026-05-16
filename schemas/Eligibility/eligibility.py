from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EligibilityDecisionBase(BaseModel):
    credit_score: Optional[int]
    monthly_income: Optional[float]
    existing_emi: Optional[float]
    proposed_emi: Optional[float]
    foir: Optional[float]
    eligibility_status: str              # ELIGIBLE / NOT_ELIGIBLE / PRE_ELIGIBLE
    rejection_reason: Optional[str]


class EligibilityDecisionCreate(EligibilityDecisionBase):
    user_id: int


class EligibilityDecisionResponse(EligibilityDecisionBase):
    id: int
    evaluated_at: datetime

    class Config:
        from_attributes = True
