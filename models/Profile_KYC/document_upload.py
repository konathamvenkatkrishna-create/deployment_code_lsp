from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, Enum as SQLEnum, Index, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class DocumentType(str, enum.Enum):
    AADHAAR_FRONT  = "AADHAAR_FRONT"
    AADHAAR_BACK   = "AADHAAR_BACK"
    PAN_CARD       = "PAN_CARD"
    SALARY_SLIP    = "SALARY_SLIP"
    BANK_STATEMENT = "BANK_STATEMENT"

class DocumentStatus(str, enum.Enum):
    UPLOADED     = "UPLOADED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED     = "APPROVED"
    REJECTED     = "REJECTED"

class DocumentUpload(Base):
    __tablename__ = "document_uploads"

    id            = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id       = Column(BigInteger, ForeignKey("user_profiles.user_id"), nullable=False, index=True)
    email         = Column(String(120), nullable=False, index=True)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_path     = Column(String(500), nullable=False)   
    file_size     = Column(Integer,     nullable=False)
    mime_type     = Column(String(100), nullable=False)
    status        = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    admin_remarks = Column(String(500), nullable=True)

    # OCR fields — populated automatically on upload
    ocr_text       = Column(Text,    nullable=True)   
    extracted_data = Column(JSONB,   nullable=True)   
    match_score    = Column(Float,   nullable=True)   
    ocr_verified   = Column(Integer, nullable=True)   # 1 = passed, 0 = failed, None = not run

    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    user = relationship("UserProfile", back_populates="documents")

    __table_args__ = (
        Index("idx_document_status", "status"),
        Index("idx_user_document",   "user_id", "document_type"),
    )