from sqlalchemy import Column, String, ForeignKey, Boolean, Integer, Text
from sqlalchemy.orm import relationship
from core.database import Base
from sqlalchemy import DateTime
from datetime import datetime

class LoanApplicationReference(Base):

    __tablename__ = "loan_application_references"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True)

    name = Column(String(100), nullable=False)
    mobile_number = Column(String(15), nullable=False)
    relation_type = Column(String(50), nullable=False)
    is_emergency_contact = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_last_sent_at = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)
    otp_hash = Column(Text, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_verified = Column(Integer, default=0)
    loan_application = relationship(
        "LoanApplication",
        back_populates="references")

    otp_records = relationship(
        "ReferenceMobileOTP",
        back_populates="reference",
        cascade="all, delete-orphan")
