from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class LenderPaymentDetails(Base):
    __tablename__ = "lender_payment_details"

    id = Column(Integer, primary_key=True, index=True)

    lender_id = Column(
        Integer,
        ForeignKey("lenders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    upi_id = Column(String, nullable=True)

    account_number = Column(String, nullable=True)
    ifsc = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)

    card_number = Column(String, nullable=True)
    card_type = Column(String, nullable=True)
    expiry = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ IMPORTANT: STRING ONLY (no import)
    lender = relationship(
        "Lender",
        back_populates="payment_details"
    )