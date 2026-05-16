from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class ForeclosureRequest(Base):
    __tablename__ = "foreclosures"

    id = Column(Integer, primary_key=True, autoincrement=True)

    application_id = Column(
        Integer,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False
    )

    outstanding = Column(Numeric(12, 2), nullable=False)
    charge      = Column(Numeric(12, 2), nullable=False)
    gst         = Column(Numeric(12, 2), nullable=False)

    # 🔥 ADD THESE
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_id   = Column(String(100), nullable=True)
    order_id     = Column(String(100), nullable=True)

    status = Column(String(20), default="PENDING")  # PENDING / SUCCESS / FAILED

    created_at = Column(DateTime, server_default=func.now())

    loan = relationship("LoanApplication", back_populates="foreclosures")