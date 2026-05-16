from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# -----------------------------
# REQUEST: Confirm Disbursement
# -----------------------------
class DisbursementConfirmRequest(BaseModel):
    loan_id: int = Field(..., gt=0, description="Loan ID")


# -----------------------------
# RESPONSE: Confirm Disbursement
# -----------------------------
class DisbursementConfirmResponse(BaseModel):
    loan_id: int
    status: str
    message: str


# -----------------------------
# RESPONSE: Get Status
# -----------------------------
class DisbursementStatusResponse(BaseModel):
    loan_id: int
    status: str
    amount: Optional[float] = None
    utr_number: Optional[str] = None
    bank_account: Optional[str] = None
    updated_at: Optional[datetime] = None