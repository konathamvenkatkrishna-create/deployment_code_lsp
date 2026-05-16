from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_event"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String, unique=True, nullable=False)
    application_id = Column(Integer, ForeignKey("loan_application.id"), nullable=False)

    source = Column(String, nullable=False, default="NBFC")
    payload = Column(Text, nullable=False)

    status = Column(String, default="PENDING",server_default="PENDING")  # PENDING / PROCESSED / FAILED


    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)