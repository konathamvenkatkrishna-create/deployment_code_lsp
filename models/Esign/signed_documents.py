from sqlalchemy import (
    Column, BigInteger, String, DateTime,
    ForeignKey, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class SignedDocument(Base):
    __tablename__ = "signed_documents"

    id = Column(BigInteger, primary_key=True, index=True)

    # =====================================================
    # 🔗 RELATIONS
    # =====================================================
    session_id = Column(
        BigInteger,
        ForeignKey("esign_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    agreement_id = Column(
        BigInteger,
        ForeignKey("agreements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    application_id = Column(   # 🔥 ADD THIS (VERY USEFUL)
        BigInteger,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # =====================================================
    # 📄 FILE DATA
    # =====================================================
    signed_pdf_path = Column(String, nullable=False)

    file_hash = Column(
        String,
        nullable=False,
        index=True   # 🔥 for verification
    )

    # =====================================================
    # ⏱ TIMESTAMP
    # =====================================================
    signed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # =====================================================
    # 🔗 RELATIONSHIPS
    # =====================================================
    session = relationship(
        "EsignSession",
        back_populates="signed_document"
    )

    agreement = relationship("Agreement")

    # =====================================================
    # 🔥 INDEXES
    # =====================================================
    __table_args__ = (
        Index("idx_signed_doc_agreement", "agreement_id"),
        Index("idx_signed_doc_application", "application_id"),
    )