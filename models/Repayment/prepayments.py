from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class PrepaymentRequest(Base):
    __tablename__ = "prepayments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id"),  # 🔥 ensure correct table name
        nullable=False
    )

    emi_numbers = Column(String, nullable=True)
    amount = Column(Numeric(12, 2))
    charge = Column(Numeric(12, 2))
    gst = Column(Numeric(12, 2))

    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())

    # optional relationship
    loan = relationship("LoanApplication", back_populates="prepayments")