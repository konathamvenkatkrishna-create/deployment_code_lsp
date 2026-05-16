from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, ForeignKey
from core.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(BigInteger, primary_key=True)

    user_id = Column(BigInteger, ForeignKey("users.id"))  # ✅ REQUIRED FIX

    mobile_number = Column(String(25), nullable=False)
    #email = Column(String(255))
    otp_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    resend_attempts = Column(Integer, default=0)
    otp_status = Column(String(20), default="PENDING")  # PENDING | VERIFIED | EXPIRED | BLOCKED
    device_id = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    blocked_until = Column(DateTime, nullable=True)
    purpose = Column(String(30),nullable=False,index=True,default="REGISTER")  # REGISTER | FORGOT_PASSWORD | LOGIN | EMAIL_VERIFY | MOBILE_VERIFY
    # REGISTER | FORGOT_PASSWORD | LOGIN | EMAIL_VERIFY | MOBILE_VERIFY

    user = relationship("User", back_populates="otp_records")  # ✅