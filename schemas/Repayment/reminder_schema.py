
from pydantic import BaseModel, validator
from typing import Optional
from datetime import time, datetime


# =====================================================
# UPDATE SCHEMA
# =====================================================
class ReminderSettingsUpdate(BaseModel):

    # Push
    push_enabled: Optional[bool] = None
    push_7_days: Optional[bool] = None
    push_3_days: Optional[bool] = None
    push_1_day: Optional[bool] = None
    push_due_today: Optional[bool] = None
    push_overdue: Optional[bool] = None

    # SMS
    sms_enabled: Optional[bool] = None
    sms_7_days: Optional[bool] = None
    sms_3_days: Optional[bool] = None
    sms_1_day: Optional[bool] = None
    sms_due_today: Optional[bool] = None
    sms_overdue: Optional[bool] = None

    # Email
    email_enabled: Optional[bool] = None
    email_7_days: Optional[bool] = None
    email_3_days: Optional[bool] = None
    email_1_day: Optional[bool] = None
    email_due_today: Optional[bool] = None
    email_overdue: Optional[bool] = None

    # Quiet hours (use proper type)
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None

    @validator("quiet_start", "quiet_end", pre=True)
    def parse_time(cls, v):
        if v is None:
            return v
        if isinstance(v, time):
            return v
        try:
            return datetime.strptime(v, "%H:%M").time()
        except:
            raise ValueError("Time must be in HH:MM format")


# =====================================================
# RESPONSE SCHEMA
# =====================================================
class ReminderSettingsResponse(BaseModel):

    push_enabled: bool
    push_7_days: bool
    push_3_days: bool
    push_1_day: bool
    push_due_today: bool
    push_overdue: bool

    sms_enabled: bool
    sms_7_days: bool
    sms_3_days: bool
    sms_1_day: bool
    sms_due_today: bool
    sms_overdue: bool

    email_enabled: bool
    email_7_days: bool
    email_3_days: bool
    email_1_day: bool
    email_due_today: bool
    email_overdue: bool

    quiet_start: Optional[time]
    quiet_end: Optional[time]

    class Config:
        orm_mode = True


# =====================================================
# REMINDER LOG SCHEMA
# =====================================================
class ReminderLogCreate(BaseModel):
    user_id: int
    emi_id: int
    channel: str
    status: str


class ReminderLogResponse(BaseModel):
    log_id: int
    user_id: int
    emi_id: int
    channel: str
    status: str
    sent_at: datetime

    class Config:
        orm_mode = True

