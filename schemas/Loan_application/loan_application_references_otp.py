from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ---------------------------
# SEND OTP (only mobile)
# ---------------------------
class ReferenceOTPSendRequest(BaseModel):
    mobile_number: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mobile_number": "9876543210"
            }
        }
    )


# ---------------------------
# VERIFY OTP (ONLY OTP)
# ---------------------------
class ReferenceOTPVerifyRequest(BaseModel):
    otp_code: str = Field(min_length=4, max_length=6)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "otp_code": "123456"
            }
        }
    )


# ---------------------------
# VERIFY RESPONSE
# ---------------------------
class ReferenceOTPVerifyResponse(BaseModel):
    reference_id: int
    verified: bool
    verified_at: datetime | None

    model_config = ConfigDict(from_attributes=True)