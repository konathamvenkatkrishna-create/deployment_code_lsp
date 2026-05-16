from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from core.enums import LoanPurpose


# =====================================================
# CREATE
# =====================================================
class LoanApplicationPurposeCreate(BaseModel):
    purpose_code: LoanPurpose
    purpose_description: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "purpose_code": "MEDICAL",
                "purpose_description": "Hospital expenses"
            }
        }
    )


# =====================================================
# UPDATE (FUTURE USE)
# =====================================================
class LoanApplicationPurposeUpdate(BaseModel):
    purpose_code: Optional[LoanPurpose] = None
    purpose_description: Optional[str] = Field(
        default=None,
        max_length=500
    )


# =====================================================
# RESPONSE (FIXED)
# =====================================================
class LoanApplicationPurposeResponse(BaseModel):
    application_id: int
    purpose_code: Optional[LoanPurpose] = None   # ✅ FIX
    purpose_description: Optional[str] = None   # ✅ FIX
    message: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# SUMMARY (OPTIONAL USE)
# =====================================================
class LoanPurposeSummary(BaseModel):
    purpose_code: Optional[LoanPurpose] = None   # ✅ FIX
    purpose_description: Optional[str] = None