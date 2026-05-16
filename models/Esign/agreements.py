from sqlalchemy import (
    Column, BigInteger, String, DateTime, Boolean,
    Enum as SqlEnum, ForeignKey, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum

from core.database import Base


# =====================================================
# 📄 AGREEMENT STATUS
# =====================================================
class AgreementStatus(str, Enum):
    GENERATED = "GENERATED"
    SIGNED = "SIGNED"


class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(BigInteger, primary_key=True, index=True)

    # 🔗 FK
    application_id = Column(
        BigInteger,
        ForeignKey("loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(BigInteger, nullable=False, index=True)

    # 📊 Versioning
    version = Column(BigInteger, default=1, nullable=False)

    # 🔄 Active flag
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    esign_status = Column(String, default="PENDING")
    # 📄 Status
    status = Column(
        SqlEnum(AgreementStatus),
        default=AgreementStatus.GENERATED,
        nullable=False,
        index=True
    )

    # 📄 Original
    agreement_pdf_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, index=True)

    # 📄 Signed
    signed_pdf_path = Column(String, nullable=True)
    signed_file_hash = Column(String, nullable=True, index=True)

    # 🔐 eSign
    provider = Column(String, nullable=True)
    esign_reference_id = Column(String, nullable=True)

    # ⏱
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # =====================================================
    # 🔗 RELATIONSHIP
    # =====================================================
    loan = relationship("LoanApplication", back_populates="agreements")

    # =====================================================
    # 🔥 INDEXES
    # =====================================================
    __table_args__ = (
        Index("idx_agreement_app_active", "application_id", "is_active"),
    )