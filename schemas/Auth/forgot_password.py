from pydantic import BaseModel, EmailStr, field_validator
from core.validators import (
    validate_mobile_number,
    validate_otp,
    validate_password,
)
class ForgotPasswordmobile(BaseModel):
    mobile: str 
    _validate_mobile = field_validator("mobile")(validate_mobile_number)
class ForgotPasswordEmail(BaseModel):
    email: EmailStr
class VerifyOtpmobile(BaseModel):
    mobile: str
    otp: str
    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_otp = field_validator("otp")(validate_otp)
class VerifyOtpEmail(BaseModel):
    email: EmailStr
    email_otp: str
    _validate_email_otp = field_validator("email_otp")(validate_otp)
class ResetPasswordMobileRequest(BaseModel):
    mobile: str
    new_password: str
    confirm_password: str
    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_password = field_validator("new_password")(validate_password)
    _validate_confirm_password = field_validator("confirm_password")(validate_password) 
class ResetPasswordEmailRequest(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str
    _validate_password = field_validator("new_password")(validate_password)
    _validate_confirm_password = field_validator("confirm_password")(validate_password)

class resendOtpMobile(BaseModel):
    mobile: str
    _validate_mobile = field_validator("mobile")(validate_mobile_number)

class resendOtpEmail(BaseModel):
    email: EmailStr