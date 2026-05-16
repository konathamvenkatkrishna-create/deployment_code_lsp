from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from core.enums import ReferenceRelation


# =====================================================
# SINGLE REFERENCE ITEM
# =====================================================
class ReferenceItem(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    mobile_number: str = Field(min_length=10, max_length=15)
    relation_type: ReferenceRelation   # ✅ FIXED (enum)
    is_emergency_contact: bool


# =====================================================
# CREATE REQUEST (JSON BODY)
# =====================================================
class LoanApplicationReferencesCreate(BaseModel):
    reference1: ReferenceItem
    reference2: ReferenceItem

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reference1": {
                    "name": "Ramesh Kumar",
                    "mobile_number": "9876543210",
                    "relation_type": "FRIEND",
                    "is_emergency_contact": True
                },
                "reference2": {
                    "name": "Suresh Rao",
                    "mobile_number": "9123456789",
                    "relation_type": "COLLEAGUE",
                    "is_emergency_contact": False
                }
            }
        }
    )


# =====================================================
# RESPONSE
# =====================================================
class LoanApplicationReferenceResponse(BaseModel):
    id: Optional[int] = None   # ✅ SAFE
    name: str
    mobile_number: str
    relation_type: ReferenceRelation   # ✅ FIXED
    is_emergency_contact: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)