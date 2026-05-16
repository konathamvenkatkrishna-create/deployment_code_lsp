from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List


class LoanStatusResponse(BaseModel):
    application_id: int
    application_status: str
    reference_number: str


# ✅ ADD THIS
class LoanStatusTimelineItem(BaseModel):
    previous_status: Optional[str]
    new_status: str
    source: str
    status_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ✅ ADD THIS
class LoanStatusTimelineResponse(BaseModel):
    total: int
    timeline: List[LoanStatusTimelineItem]