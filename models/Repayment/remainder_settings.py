from sqlalchemy import Column, Integer, Boolean, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import time


class ReminderSettings(Base):
    __tablename__ = "reminder_settings"

    id = Column(Integer, primary_key=True, index=True)  # ✅ REQUIRED

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # ── Push ─────────────────────────────────────
    push_enabled = Column(Boolean, default=True)
    push_7_days = Column(Boolean, default=True)
    push_3_days = Column(Boolean, default=True)
    push_1_day = Column(Boolean, default=True)
    push_due_today = Column(Boolean, default=True)
    push_overdue = Column(Boolean, default=True)

    # ── SMS ──────────────────────────────────────
    sms_enabled = Column(Boolean, default=True)
    sms_7_days = Column(Boolean, default=True)
    sms_3_days = Column(Boolean, default=True)
    sms_1_day = Column(Boolean, default=True)
    sms_due_today = Column(Boolean, default=True)
    sms_overdue = Column(Boolean, default=True)

    # ── Email ────────────────────────────────────
    email_enabled = Column(Boolean, default=True)
    email_7_days = Column(Boolean, default=True)
    email_3_days = Column(Boolean, default=True)
    email_1_day = Column(Boolean, default=True)
    email_due_today = Column(Boolean, default=True)
    email_overdue = Column(Boolean, default=True)

    # ── Quiet hours ──────────────────────────────
    quiet_start = Column(Time, default=time(9, 0))
    quiet_end = Column(Time, default=time(18, 0))

    # ── Relationship ─────────────────────────────
    user = relationship("User", backref="reminder_settings", uselist=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_user_reminder_settings"),
    )