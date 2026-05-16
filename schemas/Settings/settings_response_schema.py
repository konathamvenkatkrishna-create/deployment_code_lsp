from pydantic import BaseModel
from typing import Optional


class SettingsResponse(BaseModel):
    push_notification: Optional[bool] = None
    sms_notification: Optional[bool] = None
    email_notification: Optional[bool] = None

    application_updates: Optional[bool] = None
    payment_reminders: Optional[bool] = None
    promotional_offers: Optional[bool] = None
    product_updates: Optional[bool] = None

    biometric_enabled: Optional[bool] = None
    pin_enabled: Optional[bool] = None

    language: Optional[str] = None

    class Config:
        from_attributes = True