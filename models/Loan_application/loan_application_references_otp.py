from sqlalchemy import Column, DateTime, String, Boolean, ForeignKey, TIMESTAMP, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class ReferenceMobileOTP(Base):
    __tablename__ = "reference_mobile_otps"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(
        Integer,
        ForeignKey("loan_application_references.id", ondelete="CASCADE"),
        nullable=False,
        index=True)

    otp_code = Column(String(64), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False)
    ip_address = Column(String, nullable=True)
    verified_at = Column(
        DateTime(timezone=True),
        nullable=True)

    reference = relationship(
        "LoanApplicationReference",
        back_populates="otp_records")
