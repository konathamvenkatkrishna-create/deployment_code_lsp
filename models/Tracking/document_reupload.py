from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.sql import func
from core.database import Base
import enum


# ✅ Reuse SAME ENUMS for consistency
from models.Profile_KYC.document_upload import DocumentType, DocumentStatus


class ReuploadStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentReupload(Base):
    __tablename__ = "document_reupload"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 🔗 Link to original document
    document_id = Column(BigInteger, ForeignKey("document_uploads.id"), nullable=False)

    # 🔗 User reference (fast access)
    user_id = Column(BigInteger, ForeignKey("user_profiles.user_id"), nullable=False, index=True)

    # 📄 Document info (same as upload)
    document_type = Column(SQLEnum(DocumentType), nullable=False)

    # 📂 OLD FILE DETAILS (before reupload)
    old_file_name = Column(String(255), nullable=True)
    old_file_path = Column(String(500), nullable=True)

    # 📂 NEW FILE DETAILS (after reupload)
    new_file_name = Column(String(255), nullable=False)
    new_file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

    # ❌ Rejection reason from previous review
    rejection_reason = Column(String(500), nullable=True)

    # 🔄 Reupload status lifecycle
    status = Column(SQLEnum(ReuploadStatus), default=ReuploadStatus.PENDING_REVIEW)

    # 👤 Audit fields
    uploaded_by = Column(BigInteger, nullable=False)   # who reuploaded
    reviewed_by = Column(String(100), nullable=True)

    # ⏱️ timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)