from pydantic import BaseModel
from typing import Optional


class SecuritySettings(BaseModel):
    biometric_enabled: Optional[bool]
    pin_enabled: Optional[bool]