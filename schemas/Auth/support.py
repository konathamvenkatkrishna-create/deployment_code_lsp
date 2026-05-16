# app/schemas/support.py
from pydantic import BaseModel,field_validator
from typing import Optional
from core.validators import validate_username,validate_mobile_number,validate_password
class CreateSupportUserSchema(BaseModel):
    username: str
    mobile :str
    password: str
    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_username = field_validator("username")(validate_username)
    _validate_password = field_validator("password")(validate_password)


class UpdateSupportUserSchema(BaseModel):
    username: Optional[str] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    _validate_mobile = field_validator("mobile")(validate_mobile_number)
    _validate_username = field_validator("username")(validate_username)
    _validate_password = field_validator("password")(validate_password)