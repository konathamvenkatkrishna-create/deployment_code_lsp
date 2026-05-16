from pydantic import BaseModel
from typing import Optional
from schemas.Settings.settings_response_schema import SettingsResponse

class CommonResponse(BaseModel):
    success: bool
    message: str
    data: Optional[SettingsResponse] = None

    class Config:
        from_attributes = True