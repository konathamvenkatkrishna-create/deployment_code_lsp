from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ===============================
# PROFILE UPDATE SCHEMA
# ===============================
class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr]
    mobile: Optional[str] = Field(None, min_length=10, max_length=15)
    address: Optional[str] = Field(None, max_length=255)
    temporary_address: Optional[str] = Field(None, max_length=255)


# ===============================
# TEMP ADDRESS UPDATE (SEPARATE API)
# ===============================
class TempAddressUpdate(BaseModel):
    temporary_address: str = Field(..., min_length=5, max_length=255)


# ===============================
# PROFILE RESPONSE (OPTIONAL)
# ===============================
class ProfileResponse(BaseModel):
    id: int
    name: Optional[str]
    email: EmailStr
    mobile: Optional[str]
    address: Optional[str]
    temporary_address: Optional[str]
    profile_image_url: Optional[str]

    class Config:
        from_attributes = True