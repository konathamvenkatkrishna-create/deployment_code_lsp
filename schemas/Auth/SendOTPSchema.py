from pydantic import BaseModel, Field, field_validator
from typing import Optional
from core.validators import (
    validate_mobile_number,
    validate_otp,
    validate_device_id,
    validate_password,
)

# ================= SEND OTP =================
class SendOTPSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str
    mobile_number: str

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_password = field_validator("password")(validate_password)


# ================= VERIFY OTP =================
class VerifyOTPSchema(BaseModel):
    mobile_number: str
    otp: str
    device_id : str
    

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_otp = field_validator("otp")(validate_otp)


# ================= RESEND OTP =================
class ResendOTPSchema(BaseModel):
    mobile_number: str
    device_id: str

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_device = field_validator("device_id")(validate_device_id)


# ================= UPDATE USER =================
class UpdateUserSchema(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    mobile_number: Optional[str] = None
    is_active: Optional[bool] = None

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)