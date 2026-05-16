from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from core.database import Base

class UserConsent(Base):
    __tablename__ = "user_consent"

    id = Column(BigInteger, primary_key=True)

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    consent_type = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)

    accepted = Column(Boolean, nullable=False)
    scroll_completed = Column(Boolean, nullable=False)
    ip_address = Column(String(50))

    accepted_at = Column(DateTime(timezone=True), server_default=func.now(),nullable=False)

    __table_args__ = (
        Index("idx_user_consent_user_id", "user_id"),
    )
