from pydantic import BaseModel, field_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from core.validators import (
    validate_mobile_number,
    validate_password,
    validate_gst_number,
    validate_company_name,
    validate_address
)


class LenderCreate(BaseModel):
    company_name: str
    mobile_number: str
    password: str
    gst_number: Optional[str] = None
    address: Optional[str] = None
    min_credit_score: Optional[int] = None
    max_amount: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    benefits: Optional[List[str]] = None
    _validate_company = field_validator("company_name")(validate_company_name)
    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_password = field_validator("password")(validate_password)
    _validate_gst = field_validator("gst_number")(validate_gst_number)
    _validate_address = field_validator("address")(validate_address)


class LenderResponse(BaseModel):
    id: int
    user_id: int
    company_name: str

    gst_number: Optional[str] = None
    address: Optional[str] = None
    min_credit_score: Optional[int]
    max_amount: Optional[Decimal]
    interest_rate: Optional[Decimal]
    processing_fee: Optional[Decimal]
    benefits: Optional[List[str]]

    is_active: bool
    is_verified: bool
    is_blocked: bool

    created_at: datetime

    class Config:
        from_attributes = True


# ================= UPDATE =================
class LenderUpdate(BaseModel):
    company_name: Optional[str] = None
    min_credit_score: Optional[int]
    max_amount: Optional[Decimal]
    interest_rate: Optional[Decimal]
    processing_fee: Optional[Decimal]
    address: Optional[str] = None

    _validate_company = field_validator("company_name")(validate_company_name)
    _validate_address = field_validator("address")(validate_address)

class LenderStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_blocked: Optional[bool] = None
