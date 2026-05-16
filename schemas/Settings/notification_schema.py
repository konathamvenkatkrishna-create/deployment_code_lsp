from pydantic import BaseModel
from typing import Optional


class NotificationSettings(BaseModel):
    push_notification: Optional[bool]
    sms_notification: Optional[bool]
    email_notification: Optional[bool]

    application_updates: Optional[bool]
    payment_reminders: Optional[bool]
    promotional_offers: Optional[bool]
    product_updates: Optional[bool]