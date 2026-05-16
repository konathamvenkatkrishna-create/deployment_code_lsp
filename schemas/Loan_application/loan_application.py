from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from core.enums import LoanApplicationStep, LoanTenureMonths


# =====================================================
# APPLY REQUEST
# =====================================================
class LoanApplicationCreateSchema(BaseModel):

    requested_tenure_months: int

# =====================================================
# APPLY RESPONSE (ONLY DRAFT CREATION RESPONSE)
# =====================================================
class LoanApplicationCreateResponseSchema(BaseModel):
    application_id: int
    approved_amount: Decimal
    next_step: LoanApplicationStep


# =====================================================
# UPDATE SCHEMA (IF NEEDED LATER)
# =====================================================
class LoanApplicationUpdateSchema(BaseModel):
    interest_rate: Optional[Decimal] = None
    monthly_emi: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    total_repayment: Optional[Decimal] = None
    lender_name: Optional[str] = None
    current_step: Optional[str] = None


# =====================================================
# SUBMIT REQUEST
# =====================================================
class LoanSubmitRequestSchema(BaseModel):
    confirm: bool


# =====================================================
# SUBMIT RESPONSE
# =====================================================
class LoanSubmitResponseSchema(BaseModel):
    reference_number: str
    
    message: str
    expected_decision_time: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# FULL APPLICATION RESPONSE (GET APPLICATION)
# =====================================================
class LoanApplicationResponseSchema(BaseModel):
    application_id: int
    reference_number: Optional[str] = None   
    application_status: str
    current_step: str
    approved_amount: Optional[Decimal] = None
    requested_tenure_months: Optional[int] = None
    interest_rate: Optional[Decimal] = None
    lender_name: Optional[str] = None
    is_submitted: bool
    last_completed_step: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)