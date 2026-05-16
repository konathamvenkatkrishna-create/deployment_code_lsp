from pydantic import BaseModel, field_validator
from core.validators import (
    validate_mobile_number,
    validate_otp,
    validate_device_id,
    validate_password,
)


class Verify2FASchema(BaseModel):
    mobile: str
    otp: str
    device_id: str

    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_otp = field_validator("otp")(validate_otp)
    _validate_device = field_validator("device_id")(validate_device_id)


class Disable2FASchema(BaseModel):
    password: str

    _validate_password = field_validator("password")(validate_password)


class Login2FASchema(BaseModel):
    mobile: str
    password: str
    device_id: str

    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_password = field_validator("password")(validate_password)
    _validate_device = field_validator("device_id")(validate_device_id)


class Send2FASchema(BaseModel):   # ✅ FIXED NAME
    mobile: str
    device_id: str

    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_device = field_validator("device_id")(validate_device_id)


# ✅ IMPORTANT (Pydantic v2)
Verify2FASchema.model_rebuild()
Disable2FASchema.model_rebuild()
Login2FASchema.model_rebuild()
Send2FASchema.model_rebuild()