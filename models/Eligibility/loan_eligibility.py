import uuid
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    DECIMAL,
    String,
    Text,
    DateTime,
    Integer,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class LoanEligibility(Base):
    __tablename__ = "loan_eligibility"

    __table_args__ = (
        CheckConstraint(
            "eligibility_status IN ('ELIGIBLE', 'REJECTED')",
            name="loan_eligibility_status"
        ),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True, index=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )
    credit_profile_id = Column(
        BigInteger,
        ForeignKey("credit_profiles.id"),
        nullable=True
    )
    income_used  = Column(DECIMAL(12, 2), nullable=True)
    existing_emi = Column(DECIMAL(12, 2), default=0.00)
    proposed_emi = Column(DECIMAL(12, 2), nullable=True)
    foir_ratio       = Column(DECIMAL(5, 4), nullable=True)
    max_allowed_foir = Column(DECIMAL(5, 2), default=0.50)
    credit_score_used          = Column(BigInteger, nullable=True)
    previous_credit_score_used = Column(BigInteger, nullable=True)
    bureau_name                = Column(String(50), nullable=True)
    eligibility_status = Column(String(20), nullable=False)
    failure_reason     = Column(Text, nullable=True)
    max_eligible_amount = Column(DECIMAL(12, 2), default=0.00)
    max_eligible_emi    = Column(DECIMAL(12, 2), default=0.00)
    previously_checked_at = Column(DateTime, nullable=True)
    latest_checked_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", back_populates="loan_eligibilities")
    loan_application = relationship("LoanApplication", back_populates="eligibility", cascade="all, delete-orphan")
    credit_profile = relationship("CreditProfile",foreign_keys=[credit_profile_id],lazy="select")