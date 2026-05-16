from sqlalchemy import (
    Column, BigInteger, String, DateTime,
    ForeignKey, JSON, Enum as SqlEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from core.database import Base


# =====================================================
# 🔐 EVENT TYPES (CLEANED)
# =====================================================
class EsignEventType(str, Enum):
    INITIATED = "INITIATED"
    OTP_SENT = "OTP_SENT"
    OTP_VERIFIED = "OTP_VERIFIED"
    SIGNED = "SIGNED"
    FAILED = "FAILED"


class EsignAuditLog(Base):
    __tablename__ = "esign_audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)

    # 🔗 Session reference
    session_id = Column(
        BigInteger,
        ForeignKey("esign_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 🔗 Application reference (ADD FK)
    application_id = Column(
        BigInteger,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(BigInteger, nullable=False, index=True)

    # 🔄 Event type
    event_type = Column(
        SqlEnum(EsignEventType),
        nullable=False,
        index=True
    )

    event_description = Column(String, nullable=True)

    # 📊 Metadata (payload, errors, etc.)
    event_metadata = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================================
    # 🔗 RELATIONSHIPS
    # =====================================================
    session = relationship("EsignSession", back_populates="audit_logs")

    # =====================================================
    # 🔥 INDEXES
    # =====================================================
    __table_args__ = (

        # Fast lookup per session + event
        Index("idx_esign_audit_session_event", "session_id", "event_type"),

        # Fast timeline queries
        Index("idx_esign_audit_created", "created_at"),
    )