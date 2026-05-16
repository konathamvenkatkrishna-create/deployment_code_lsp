from pydantic import BaseModel, Field
from typing import Optional


class RejectRequestSchema(BaseModel):
    rejection_reason: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Reason for rejecting the loan application"
    )


class RejectResponseSchema(BaseModel):
    success: bool
    message: str
    application_id: int
    status: str
    rejection_reason: Optional[str] = None