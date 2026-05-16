from pydantic import BaseModel, Field, field_validator
from typing import Optional


# =====================================================
# 🔐 INITIATE (NO INPUT FROM USER)
# =====================================================
class InitiateRequest(BaseModel):
    """
    No input required.
    Loan + Aadhaar will be fetched from DB using current_user
    """
    pass


class InitiateResponse(BaseModel):
    transaction_id: str
    masked_aadhaar: str


# =====================================================
# 🔐 VERIFY OTP
# =====================================================
class VerifyRequest(BaseModel):
    transaction_id: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class VerifyResponse(BaseModel):
    signed_pdf: Optional[str] = None
    file_hash: Optional[str] = None
    status: str