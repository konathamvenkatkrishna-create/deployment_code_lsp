from sqlalchemy import Column, BigInteger, ForeignKey, String, DateTime, DECIMAL, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class CreditProfile(Base):
    __tablename__ = "credit_profiles"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger,ForeignKey("users.id"),nullable=False)
    pan_number = Column(String(10))
    bureau_name         = Column(String(50), nullable=False)
    credit_score        = Column(BigInteger, nullable=False)
    report_reference_id = Column(String(100), nullable=True)
    pull_type = Column(String(10))
    total_active_loans = Column(BigInteger, default=0)
    total_existing_emi = Column(DECIMAL(12, 2), default=0.00)
    bureau_raw_response = Column(JSON, nullable=True)
    pulled_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    accounts = relationship("CreditAccount",back_populates="credit_profile",cascade="all, delete-orphan",lazy="select")

    user = relationship(
        "User",
        back_populates="credit_profiles"
    )