from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Index, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from core.database import Base

class KYCPANVerification(Base):
    __tablename__ = "kyc_pan_verifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    pan_number = Column(String(10),  nullable=False)
    full_name_submitted = Column(String(150), nullable=False, default="")
    verified_name = Column(String(150), nullable=False, default="")
    match_percentage = Column(Float, nullable=True)
    name_match = Column(Boolean, nullable=False, default=False)
    status = Column(String(20),  nullable=False)
    failure_reason = Column(String(200), nullable=True)
    attempt_number= Column(Integer,     nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    user = relationship("UserProfile", back_populates="pan_verifications")

    __table_args__ = (
        Index("idx_pan_status", "status"),
        Index("idx_user_pan",   "user_id", "pan_number"),
    )