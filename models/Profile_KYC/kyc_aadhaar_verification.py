from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Index, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from core.database import Base

class KYCAadhaarVerification(Base):
    __tablename__ = "kyc_aadhaar_verifications"

    id  = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id  = Column(BigInteger, ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    aadhaar_number = Column(String(12), nullable=False)
    dob_submitted = Column(String(20), nullable=False, default="")
    verified_dob = Column(String(20), nullable=False, default="")
    dob_match = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False)
    failure_reason = Column(String(200), nullable=True)
    attempt_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    verified_at    = Column(DateTime(timezone=True), nullable=True)

    user = relationship("UserProfile", back_populates="aadhaar_verifications")

    __table_args__ = (
        Index("idx_aadhaar_status", "status"),
        Index("idx_user_aadhaar",   "user_id", "aadhaar_number"),
    )
