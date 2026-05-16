from sqlalchemy import Column, String, Float, BigInteger, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class LoanCalcStatus(str, enum.Enum):
    CHECKED = "CHECKED"
    APPLIED = "APPLIED"


class LoanCalculation(Base):
    __tablename__ = "loan_calculations"
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        index=True
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="select",
    )
    requested_amount = Column(Float,   nullable=False)
    tenure_months    = Column(Integer, nullable=False)
    eligible_amount  = Column(Float,   nullable=False)
    interest_rate_pa = Column(Float,   nullable=False, default=12.0)
    monthly_emi      = Column(Float,   nullable=False)
    total_repayment  = Column(Float,   nullable=False)
    total_interest   = Column(Float,   nullable=False)
    status = Column(
        Enum(
            LoanCalcStatus,
            name="loancalcstatus",
            values_callable=lambda e: [item.value for item in e],
        ),
        nullable=False,
        default=LoanCalcStatus.CHECKED
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    previously_calculated = Column(
        DateTime(timezone=True),
        nullable=True
    )