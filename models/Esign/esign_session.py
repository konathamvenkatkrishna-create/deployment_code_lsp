from sqlalchemy import (
    Column, BigInteger, String, DateTime, JSON,
    Enum as SqlEnum, ForeignKey, Index, UniqueConstraint,Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from core.database import Base


# =====================================================
# 🔐 ESIGN STATUS (CLEANED FLOW)
# =====================================================
class EsignStatus(str, Enum):
    INITIATED = "INITIATED"
    OTP_SENT = "OTP_SENT"
    IN_PROGRESS = "IN_PROGRESS"
    SIGNED = "SIGNED"
    FAILED = "FAILED"


class EsignSession(Base):
    __tablename__ = "esign_sessions"

    id = Column(BigInteger, primary_key=True, index=True)

    # 🔗 FK
    application_id = Column(
        BigInteger,
        ForeignKey("loan_application.id"),
        nullable=False,
        index=True
    )

    agreement_id = Column(
        BigInteger,
        ForeignKey("agreements.id"),
        nullable=False,
        index=True
    )

    user_id = Column(BigInteger, nullable=False, index=True)

    # 🌐 External provider txn id
    transaction_id = Column(String, unique=True, nullable=False, index=True)

    # 🔁 Payload tracking
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=True)
    callback_payload = Column(JSON, nullable=True)

    # 🔄 Status
    status = Column(
        SqlEnum(EsignStatus),
        default=EsignStatus.INITIATED,
        index=True
    )

    # 🔐 Provider
    provider = Column(String, nullable=True)

    # 📄 Quick access (important for performance)
    signed_pdf_path = Column(String, nullable=True)
    signed_file_hash = Column(String, nullable=True)

    # 🧾 Idempotency marker
    callback_processed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)
    # =====================================================
    # 🔗 RELATIONSHIPS
    # =====================================================
    signed_document = relationship(
        "SignedDocument",
        back_populates="session",
        uselist=False
    )

    audit_logs = relationship("EsignAuditLog", back_populates="session")

    # =====================================================
    # 🔥 CONSTRAINTS + INDEXES
    # =====================================================
    __table_args__ = (

        # 🚫 Only ONE active session per agreement (OTP_SENT / IN_PROGRESS)
        UniqueConstraint(
            "agreement_id",
            "status",
            name="uq_esign_active_session"
        ),

        # 🚀 Faster queries
        Index("idx_esign_app_status", "application_id", "status"),
    )