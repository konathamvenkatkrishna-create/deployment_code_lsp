from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, DECIMAL, Boolean, Index, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column( BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, autoincrement=False)
    full_name = Column(String(150), nullable=False)
    dob = Column(Date, nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    permanent_address = Column(String(500), nullable=False)     
    temporary_address = Column(String(500), nullable=True) 
    employment_type = Column(String(50), nullable=False)
    monthly_income = Column(DECIMAL(12, 2), nullable=False)
    aadhaar_number = Column(String(12), unique=True, nullable=False, index=True)
    pan_number = Column(String(10), unique=True, nullable=False, index=True)
    verified_name = Column(String(150), nullable=True)
    profile_status = Column(String(20), default="PROFILE_COMPLETED", nullable=False)
    profile_image_url = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    pan_status = Column(String(20), default="PENDING", nullable=False)
    aadhaar_status = Column(String(20), default="PENDING", nullable=False)
    bank_status = Column(String(20), default="PENDING", nullable=False)
    document_status = Column(String(20), default="PENDING", nullable=False)
    kyc_status = Column(String(20), default="INCOMPLETE", nullable=False)
    pan_locked     = Column(Boolean, default=False, nullable=False)
    aadhaar_locked = Column(Boolean, default=False, nullable=False)
    dob_locked     = Column(Boolean, default=False, nullable=False)
    name_locked    = Column(Boolean, default=False, nullable=False)
    bank_locked    = Column(Boolean, default=False, nullable=False)
    permanent_address_locked = Column(Boolean, default=False, nullable=False)
    pan_verified_at     = Column(DateTime(timezone=True), nullable=True)
    aadhaar_verified_at = Column(DateTime(timezone=True), nullable=True)
    bank_verified_at    = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),nullable=False)


    user = relationship("User",back_populates="profile")
    pan_verifications = relationship("KYCPANVerification", back_populates="user",foreign_keys="[KYCPANVerification.user_id]",cascade="all, delete-orphan", lazy="select",)
    aadhaar_verifications = relationship("KYCAadhaarVerification", back_populates="user",foreign_keys="[KYCAadhaarVerification.user_id]",cascade="all, delete-orphan", lazy="select",)
    bank_verifications = relationship("KYCBankVerification", back_populates="user",foreign_keys="[KYCBankVerification.user_id]",cascade="all, delete-orphan", lazy="select",order_by="KYCBankVerification.created_at")
    documents = relationship("DocumentUpload", back_populates="user",foreign_keys="[DocumentUpload.user_id]",cascade="all, delete-orphan", lazy="select",)
    loan_application = relationship(
    "LoanApplication",
    primaryjoin="LoanApplication.user_profile_id == UserProfile.user_id",
    back_populates="user_profile")

    __table_args__ = (
        Index("idx_status_composite", "pan_status", "aadhaar_status", "bank_status"),
        Index("idx_kyc_status",       "kyc_status"),
    )
