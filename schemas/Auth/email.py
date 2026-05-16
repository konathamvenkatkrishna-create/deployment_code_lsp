from pydantic import BaseModel, EmailStr


class SendEmail2FASchema(BaseModel):
    email: EmailStr
    device_id: str


class VerifyEmail2FASchema(BaseModel):
    email: EmailStr
    otp: str
    device_id: str


class LoginEmail2FASchema(BaseModel):
    mobile: str
    password: str
    device_id: str


class DisableEmail2FASchema(BaseModel):
    password: str


# ✅ REQUIRED for Pydantic v2 (VERY IMPORTANT)
SendEmail2FASchema.model_rebuild()
VerifyEmail2FASchema.model_rebuild()
LoginEmail2FASchema.model_rebuild()
DisableEmail2FASchema.model_rebuild()