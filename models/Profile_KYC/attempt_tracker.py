from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum, Index, UniqueConstraint,BigInteger
from core.database import Base
from datetime import datetime,timezone
import enum

class VerificationType(str, enum.Enum):
    PAN = "PAN"
    AADHAAR = "AADHAAR"
    BANK = "BANK"

class AttemptTracker(Base):
    __tablename__ = "verification_attempt_trackers"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(120), nullable=False, index=True)
    verification_type = Column(SQLEnum(VerificationType), nullable=False, index=True)
    attempts_count = Column(Integer, nullable=False, default=0)
    locked_until      = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    first_attempt_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_attempt_at   = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


    __table_args__ = (
        UniqueConstraint( "email","verification_type",name="uq_email_verification_type"),
        Index("idx_locked_until", "locked_until"),
        Index("idx_last_attempt", "last_attempt_at"),
    )

    