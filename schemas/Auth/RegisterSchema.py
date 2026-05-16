from pydantic import BaseModel, field_validator,EmailStr
from core.validators import (
    validate_mobile_number,
    validate_username,
    validate_password,
    validate_device_id
)

class RegisterSchema(BaseModel):
    mobile_number: str
    username: str
    password: str
    device_id: str

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_username = field_validator("username")(validate_username)
    _validate_password = field_validator("password")(validate_password)
    _validate_device = field_validator("device_id")(validate_device_id)
class sendotpschema(BaseModel):
    mobile_number: str
    username: str
    password: str
    device_id: str
    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_username = field_validator("username")(validate_username)
    _validate_password = field_validator("password")(validate_password)
    _validate_device = field_validator("device_id")(validate_device_id)
class LoginSchema(BaseModel):
    mobile_number: str
    password: str

    _validate_mobile = field_validator("mobile_number")(validate_mobile_number)
    _validate_password = field_validator("password")(validate_password)