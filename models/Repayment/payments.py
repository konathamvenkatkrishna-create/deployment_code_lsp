from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base
import enum
from sqlalchemy.orm import relationship


class Payment_Transaction(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True)

    # 🔹 Razorpay order_id (for initiate)
    order_id = Column(String(50), nullable=True, index=True)

    # 🔹 Razorpay payment_id (final transaction)
    transaction_id = Column(String(50), unique=True, nullable=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id"),
        index=True
    )

    emi_number = Column(String, nullable=True)

    amount_paid = Column(Numeric(12, 2), default=0)

    payment_mode = Column(String(30))
    payment_option = Column(String(20))

    # 🔥 NEW: status tracking
    status = Column(String(20), default="INITIATED")  
    # values: INITIATED, FAILED, SUCCESS, RETRY

    # 🔥 NEW: retry tracking
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    loan = relationship("LoanApplication", back_populates="payments")




