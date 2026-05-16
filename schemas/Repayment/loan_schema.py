from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
from core.enums import LoanApplicationStatus

class LoanApplicationBase(BaseModel):
    approved_amount: Decimal
    requested_tenure_months: int
    interest_rate: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None

class LoanApplicationCreate(LoanApplicationBase):
    user_id: int

class LoanApplicationUpdate(BaseModel):
    approved_amount: Optional[Decimal] = None
    requested_tenure_months: Optional[int] = None
    interest_rate: Optional[Decimal] = None
    application_status: Optional[LoanApplicationStatus] = None

class UserResponse(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        orm_mode = True

class LoanApplicationResponse(BaseModel):
    id: int
    user_id: Optional[int]
    reference_number: Optional[str]
    approved_amount: Decimal
    requested_tenure_months: int
    outstanding_amount: Optional[Decimal]
    interest_rate: Optional[Decimal]
    monthly_emi: Optional[Decimal]
    processing_fee: Optional[Decimal]
    gst_amount: Optional[Decimal]
    total_repayment: Optional[Decimal]
    disbursed_at: Optional[datetime]
    application_status: LoanApplicationStatus
    created_at: datetime
    approved_at: Optional[datetime]

    class Config:
        orm_mode = True