from sqlalchemy import DECIMAL, JSON, Column, Integer, String, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
from models.Repayment.lender_payment_details import LenderPaymentDetails
class Lender(Base):
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)   
    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    company_name = Column(String, nullable=False)
    min_credit_score = Column(Integer)
    max_amount = Column(DECIMAL(12, 2))
    interest_rate = Column(DECIMAL(5, 2))
    processing_fee = Column(DECIMAL(5, 2))
    gst_number = Column(String, nullable=True,unique=True)
    address = Column(String, nullable=True)
    benefits = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="lenders"
    )

    # ✅ optional audit relations
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    loan_application = relationship(
        "LoanApplication",
        back_populates="lender")

    payment_details = relationship(
    "LenderPaymentDetails",
    back_populates="lender",
    uselist=False,              # 🔥 one-to-one relationship
    cascade="all, delete-orphan"
)