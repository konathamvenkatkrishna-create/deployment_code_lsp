from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date
from decimal import Decimal
import re
class UserRegistrationRequest(BaseModel):                                   
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    dob: date
    permanent_address: str = Field(..., min_length=10, description="As per Aadhaar")
    temporary_address: str= Field(None, min_length=10)
    employment_type: str = Field(..., min_length=3, max_length=50)
    monthly_income: Decimal = Field(..., gt=0)
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    pan_number: str= Field(..., min_length=10, max_length=10)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: EmailStr) -> EmailStr:
        blocked_emails = ["user@example.com", "test@test.com", "example@example.com",
                          "demo@demo.com", "admin@admin.com"]
        if v.lower() in blocked_emails:
            raise ValueError(f"The email '{v}' is not allowed. Please use a valid email address.")
        return v

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Aadhaar number must contain only digits")
        if len(v) != 12:
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v

    @field_validator("dob")
    @classmethod
    def validate_age(cls, v: date) -> date:
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("User must be at least 18 years old")
        return v
    
    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Employment type is required")
        return v

    @field_validator("monthly_income")
    @classmethod
    def validate_monthly_income(cls, v: Decimal) -> Decimal:
        if v <= 1:
            raise ValueError("Enter monthly income")
        return v

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", v):
            raise ValueError("Invalid PAN format")
        return v

class UserRegistrationResponse(BaseModel):
    user_id: int
    message: str
    pan_status: str
    aadhaar_status:str
    bank_status: str
    document_status: str
    kyc_status: str
    next_step: str

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    pan_number: Optional[str] = Field(None, min_length=10, max_length=10)
    aadhaar_number: Optional[str]  = Field(None, min_length=12, max_length=12)
    dob: Optional[date] = None
    temporary_address: Optional[str] = Field(None, min_length=10)
    employment_type: Optional[str]  = Field(None, min_length=3, max_length=50)
    monthly_income: Optional[Decimal] = Field(None, gt=0)

    @field_validator("pan_number")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", v):
            raise ValueError("Invalid PAN format")
        return v

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Aadhaar number must contain only digits")
        if len(v) != 12:
            raise ValueError("Aadhaar number must be exactly 12 digits")
        return v

class UserProfileUpdateData(BaseModel):
    updated_fields: List[str]
    user_id: int
    email: str

class UserProfileUpdateResponse(BaseModel):
    success: bool
    message: str
    data: UserProfileUpdateData