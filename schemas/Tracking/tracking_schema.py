from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ApplicationTrackingResponse(BaseModel):

    application_id: int
    reference_number: Optional[str]
    status: str
    approved_amount: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True