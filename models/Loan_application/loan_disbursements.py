from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
from core.enums import DisbursementStatusEnum, PaymentModeEnum


class LoanDisbursement(Base):
    __tablename__ = "loan_disbursements"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    payment_reference_id = Column(String, nullable=True)
    payment_status = Column(
        Enum(DisbursementStatusEnum),
        default=DisbursementStatusEnum.INITIATED,
        nullable=False,
        index=True)

    payment_mode = Column(
        Enum(PaymentModeEnum),
        nullable=False)

    initiated_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    loan_application = relationship(
        "LoanApplication",
        back_populates="disbursements")
