from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False)

    application_id = Column(Integer, nullable=True)

    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    channel = Column(String, default="IN_APP")  # IN_APP / SMS
    type = Column(String, default="STATUS_UPDATE")  # STATUS_UPDATE / DOCUMENT / NBFC

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String, default="SENT")  # SENT / FAILED

    created_at = Column(DateTime(timezone=True), server_default=func.now())