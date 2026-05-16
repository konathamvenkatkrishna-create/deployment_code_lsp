from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# =====================================================
# 📋 LIST RESPONSE (USED IN DASHBOARD)
# =====================================================
class LenderApplicationListResponse(BaseModel):
    application_id: int = Field(alias="id")   # maps app.id → application_id
    reference_number: str
    approved_amount: float

    # 🔥 FIX: map DB field → API field
    tenure_months: int = Field(alias="requested_tenure_months")

    application_status: str

    # ⚠️ SAFE: allow null values
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True   # allows alias mapping


# =====================================================
# 📄 DETAIL RESPONSE
# =====================================================
class LenderApplicationDetailResponse(BaseModel):
    id: int = Field(alias="id")
    reference_number: str
    approved_amount: float
    requested_tenure_months: int
    interest_rate: float
    application_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 🏢 LENDER INFO RESPONSE
# =====================================================
class LenderResponse(BaseModel):
    id: int
    company_name: str
    gst_number: Optional[str] = None
    address: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True