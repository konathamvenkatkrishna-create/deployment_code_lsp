from sqlalchemy.orm import Session
from datetime import time, datetime
from models.Repayment.remainder_settings import ReminderSettings 
 
 
class ReminderSettingsService:
 
    @staticmethod
    def get_or_create(user_id: int, db: Session) -> ReminderSettings:
        settings = db.query(ReminderSettings).filter_by(user_id=user_id).first()
 
        if not settings:
            settings = ReminderSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
 
        return settings
 
    @staticmethod
    def update(settings: ReminderSettings, payload: dict, db: Session):
        for field, value in payload.items():
            if field in ("quiet_start", "quiet_end") and isinstance(value, str):
                h, m = map(int, value.split(":"))
                value = time(h, m)
 
            setattr(settings, field, value)
 
        db.commit()
        db.refresh(settings)
        return settings
 
    @staticmethod
    def is_within_allowed_time(settings: ReminderSettings) -> bool:
        now = datetime.now().time()
        return settings.quiet_start <= now <= settings.quiet_end
 
    @staticmethod
    def should_send_push(settings: ReminderSettings, stage: str) -> bool:
        if not settings.push_enabled:
            return False
 
        return {
            "PRE_DUE_7": settings.push_7_days,
            "PRE_DUE_3": settings.push_3_days,
            "PRE_DUE_1": settings.push_1_day,
            "DUE_TODAY": settings.push_due_today,
        }.get(stage, settings.push_overdue)
 
    @staticmethod
    def should_send_sms(settings, stage):
        if not settings.sms_enabled:
            return False
        return {
            "PRE_DUE_7": settings.sms_7_days,
            "PRE_DUE_3": settings.sms_3_days,
            "PRE_DUE_1": settings.sms_1_day,
            "DUE_TODAY": settings.sms_due_today,
        }.get(stage, settings.sms_overdue)
 
    @staticmethod
    def should_send_email(settings, stage):
        if not settings.email_enabled:
            return False
        return {
            "PRE_DUE_7": settings.email_7_days,
            "PRE_DUE_3": settings.email_3_days,
            "PRE_DUE_1": settings.email_1_day,
            "DUE_TODAY": settings.email_due_today,
        }.get(stage, settings.email_overdue)