from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# =====================================================
# CREATE SCHEMA
# =====================================================
class LoanApplicationDeclarationCreate(BaseModel):
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool
    consent_data_sharing: bool
    agreed_terms: bool = Field(..., description="User agreed to T&C")
    consent_credit_check: bool = Field(..., description="Credit bureau consent")
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=255)
    terms_version: str = Field(..., max_length=20)
    privacy_policy_version: str = Field(..., max_length=20)


# =====================================================
# UPDATE SCHEMA
# =====================================================
class LoanApplicationDeclarationUpdate(BaseModel):
    has_existing_loans: Optional[bool] = None
    has_credit_card: Optional[bool] = None
    has_default_history: Optional[bool] = None
    agreed_terms: Optional[bool] = None
    consent_credit_check: Optional[bool] = None
    consent_data_sharing: Optional[bool] = None


# =====================================================
# RESPONSE (FLAT DECLARATION)
# =====================================================
class LoanApplicationDeclarationResponse(BaseModel):
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool
    agreed_terms: bool
    consent_credit_check: bool
    consent_timestamp: datetime  # ✅ removed alias confusion
    ip_address: Optional[str]
    user_agent: Optional[str]

    model_config = ConfigDict(
        from_attributes=True
    )


# =====================================================
# WRAPPER RESPONSE (IMPORTANT FIX)
# =====================================================
class LoanApplicationDeclarationWrapperResponse(BaseModel):
    application_id: int
    current_step: str
    next_step: str
    data: LoanApplicationDeclarationResponse
    message: str


# =====================================================
# SUMMARY RESPONSE
# =====================================================
class DeclarationSummary(BaseModel):
    agreed_terms: bool
    consent_credit_check: bool
    consent_timestamp: datetime
    has_existing_loans: bool
    has_credit_card: bool
    has_default_history: bool

    model_config = ConfigDict(from_attributes=True)