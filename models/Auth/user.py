from datetime import datetime

from sqlalchemy import  Boolean, Column, BigInteger,String, Text
from core.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(50), unique=False)
    mobile_number = Column(String(25), unique=True)
    password_hash = Column(String)
    device_id = Column(Text, nullable=True)
    role = Column(String, default="USER")
    Created_at = Column(String, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_password_locked = Column(Boolean, default=False)
    biometric_enabled = Column(Boolean, default=False)
    biometric_type = Column(String(20),nullable=True) #fingerprint/faceid
    two_factor_enabled = Column(Boolean, default=False)
    biometric_key = Column(Text, nullable=True)  # public key

    profile = relationship(
    "UserProfile",
    primaryjoin="User.id == foreign(UserProfile.user_id)",
    back_populates="user",
    uselist=False)
    credit_profiles = relationship("CreditProfile", back_populates="user",cascade="all, delete-orphan")
    loan_eligibilities = relationship("LoanEligibility",back_populates="user",cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    devices = relationship("UserDevice", back_populates="user")
    lenders = relationship(
        "Lender",
        foreign_keys="Lender.user_id",
        back_populates="user")
    otp_records = relationship("OTPVerification", back_populates="user")