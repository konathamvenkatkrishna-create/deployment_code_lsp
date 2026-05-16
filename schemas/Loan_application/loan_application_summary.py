from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

from core.enums import LoanApplicationStep
from core.Loan_calculator import MIN_LOAN_AMOUNT, MAX_LOAN_AMOUNT


# =====================================================
# USER
# =====================================================
class UserSummarySchema(BaseModel):
    user_id: Optional[int] = None
    full_name: str
    mobile_number: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# ELIGIBILITY
# =====================================================
class EligibilitySummarySchema(BaseModel):
    eligible: bool
    max_loan_amount: Decimal
    approved_interest_rate: Decimal

    class Config:
        from_attributes = True


# =====================================================
# LOAN DETAILS
# =====================================================
class LoanDetailsSummarySchema(BaseModel):

    approved_amount: Decimal
    requested_tenure_months: int
    class Config:
        from_attributes = True


# =====================================================
# PURPOSE
# =====================================================
class LoanPurposeSummarySchema(BaseModel):
    purpose: str

    class Config:
        from_attributes = True


# =====================================================
# REFERENCES
# =====================================================
class ReferenceSummarySchema(BaseModel):
    name: str
    relationship: str
    mobile_number: str
    is_mobile_verified: bool

    class Config:
        from_attributes = True


class ReferencesStatusSchema(BaseModel):
    total_required: int = 2
    total_added: int
    verified_count: int
    remaining_to_verify: int

    class Config:
        from_attributes = True


# =====================================================
# DECLARATION (FIXED)
# =====================================================
class DeclarationSummarySchema(BaseModel):
    has_existing_loans: Optional[bool] = None
    has_credit_card: Optional[bool] = None
    has_default_history: Optional[bool] = None
    declaration_accepted: Optional[bool] = None

    class Config:
        from_attributes = True


# =====================================================
# SUBMISSION
# =====================================================
class SubmissionStatusSchema(BaseModel):
    last_completed_step: Optional[LoanApplicationStep] = None
    can_submit: bool
    pending_steps: List[str]

    class Config:
        from_attributes = True


# =====================================================
# FINAL RESPONSE
# =====================================================
class LoanApplicationSummaryResponseSchema(BaseModel):
    application_id: int
    user: UserSummarySchema
    eligibility: Optional[EligibilitySummarySchema] = None
    loan_details: LoanDetailsSummarySchema
    purpose: LoanPurposeSummarySchema
    references: List[ReferenceSummarySchema]
    reference_status: ReferencesStatusSchema
    declaration: DeclarationSummarySchema
    submission_status: SubmissionStatusSchema

    class Config:
        from_attributes = True


# =====================================================
# EDIT LOAN DETAILS
# =====================================================
class EditLoanDetailsSchema(BaseModel):
    approved_amount: Optional[Decimal] = Field(
        None,
        ge=MIN_LOAN_AMOUNT,
        le=MAX_LOAN_AMOUNT,
        description=f"Loan amount between ₹{MIN_LOAN_AMOUNT} and ₹{MAX_LOAN_AMOUNT}"
    )

    requested_tenure_months: Optional[int] = Field(
        None,
        description="Tenure: 3, 6, 9, or 12 months"
    )

    class Config:
        from_attributes = True


# =====================================================
# EDIT PURPOSE
# =====================================================
class EditLoanPurposeSchema(BaseModel):
    purpose_code: str = Field(...)
    purpose_description: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# EDIT REFERENCES
# =====================================================
class EditSingleReferenceSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    mobile_number: str = Field(..., min_length=10, max_length=10)
    relation_type: str
    is_emergency_contact: Optional[bool] = False

    class Config:
        from_attributes = True


class EditReferenceSchema(BaseModel):
    references: List[EditSingleReferenceSchema] = Field(
        ...,
        min_length=2,
        max_length=2
    )

    class Config:
        from_attributes = True


# =====================================================
# EDIT DECLARATION
# =====================================================
class EditDeclarationSchema(BaseModel):
    agreed_terms: bool
    consent_credit_check: bool
    consent_data_sharing: bool
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool
    terms_version: str
    privacy_policy_version: str

    class Config:
        from_attributes = True


# =====================================================
# EDIT RESPONSE
# =====================================================
class EditFieldResponseSchema(BaseModel):
    success: bool
    message: str
    updated_fields: List[str]
    application_id: int
    step_reset_to: Optional[str] = None

    class Config:
        from_attributes = True