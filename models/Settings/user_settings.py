from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, DateTime
from datetime import datetime
from core.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    biometric_enabled = Column(Boolean, default=False, nullable=False)
    pin_enabled = Column(Boolean, default=False, nullable=False)
    account_locked = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False)

    language = Column(String, default="en")

    push_notification = Column(Boolean, default=True)
    sms_notification = Column(Boolean, default=True)
    email_notification = Column(Boolean, default=True)


# 🔥 ADD THIS BELOW (same file)
class DeleteAccountRequest(Base):
    __tablename__ = "delete_account_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)