from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from datetime import datetime

from core.database import Base


class LoanTransaction(Base):
    __tablename__ = "loan_transactions"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(Integer, ForeignKey("loan_application.id"), nullable=False)
    disbursement_id = Column(Integer, ForeignKey("loan_disbursements.id"), nullable=True)

    transaction_type = Column(String(50))  # DISBURSEMENT / REFUND / FEE
    amount = Column(Numeric(12, 2))

    status = Column(String(50))  # INITIATED / SUCCESS / FAILED
    payment_mode = Column(String(50))

    reference_id = Column(String(255))
    remarks = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)