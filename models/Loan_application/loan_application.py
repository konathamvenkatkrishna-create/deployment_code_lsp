from sqlalchemy import (
    Column, Integer, Numeric, String, Boolean,
    TIMESTAMP, Enum, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base
from core.enums import LoanApplicationStatus, DisbursementStatusEnum


class LoanApplication(Base):
    __tablename__ = "loan_application"

    # =====================================================
    # 🔑 PRIMARY KEY
    # =====================================================
    id = Column(Integer, primary_key=True, index=True)

    # =====================================================
    # 🔗 FOREIGN KEYS
    # =====================================================
    user_profile_id = Column(
        Integer,
        ForeignKey("user_profiles.user_id"),
        nullable=False  # ✅ FIXED
    )

    eligibility_id = Column(
        Integer,
        ForeignKey("loan_eligibility.id"),
        nullable=False
    )

    lender_id = Column(
        Integer,
        ForeignKey("lenders.id"),
        nullable=True
    )

    # =====================================================
    # 🏦 LENDER SNAPSHOT
    # =====================================================
    lender_name = Column(String(100), nullable=True)

    # =====================================================
    # 💰 CORE LOAN FIELDS
    # =====================================================
    reference_number = Column(String(20), unique=True, index=True)

    approved_amount = Column(Numeric(12, 2), nullable=False)
    requested_tenure_months = Column(Integer, nullable=True)

    interest_rate = Column(Numeric(5, 2), nullable=True)
    monthly_emi = Column(Numeric(12, 2), nullable=True)

    processing_fee = Column(Numeric(10, 2), nullable=True)
    gst_amount = Column(Numeric(10, 2), nullable=True)

    total_repayment = Column(Numeric(14, 2), nullable=True)
    disbursed_amount = Column(Numeric(12, 2), nullable=True)

    # =====================================================
    # 🔄 FLOW TRACKING
    # =====================================================
    current_step = Column(String(50), nullable=False, default="OPENED")

    application_status = Column(
        Enum(LoanApplicationStatus, name="loan_application_status_enum"),
        default=LoanApplicationStatus.DRAFT,
        nullable=False
    )

    payout_status = Column(
        Enum(DisbursementStatusEnum),
        default=DisbursementStatusEnum.PENDING,
        nullable=False
    )

    # =====================================================
    # 🔄 CONTROL FLAGS
    # =====================================================
    is_submitted = Column(Boolean, nullable=False, default=False)

    rejection_reason = Column(String(255), nullable=True)

    lender_decision = Column(String(20), nullable=True)
    lender_decision_at = Column(TIMESTAMP, nullable=True)

    # =====================================================
    # 💸 DISBURSEMENT TRACKING
    # =====================================================
    disbursement_attempts = Column(Integer, default=0)
    last_disbursement_attempt_at = Column(TIMESTAMP, nullable=True)

    # =====================================================
    # ⏱ TIMESTAMPS
    # =====================================================
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    submitted_at = Column(TIMESTAMP, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    approved_at = Column(TIMESTAMP, nullable=True)
    rejected_at = Column(TIMESTAMP, nullable=True)
    disbursed_at = Column(TIMESTAMP, nullable=True)

    # =====================================================
    # 🔗 RELATIONSHIPS
    # =====================================================

    # 👤 User
    user_profile = relationship(
        "UserProfile",
        primaryjoin="LoanApplication.user_profile_id == UserProfile.user_id",
        back_populates="loan_application"
    )

    # 📄 Agreement (NEW - IMPORTANT)
    agreements = relationship(
        "Agreement",
        back_populates="loan",
        cascade="all, delete-orphan"
    )

    # 📊 Purpose
    purpose = relationship(
        "LoanApplicationPurpose",
        back_populates="loan_application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 📞 References
    references = relationship(
        "LoanApplicationReference",
        back_populates="loan_application",
        cascade="all, delete-orphan"
    )

    # 📜 Declaration
    declaration = relationship(
        "LoanApplicationDeclaration",
        back_populates="loan_application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 📍 Step tracker
    step_tracker = relationship(
        "LoanApplicationStepTracker",
        back_populates="loan_application",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 📊 Eligibility
    eligibility = relationship(
        "LoanEligibility",
        back_populates="loan_application"
    )

    # 🏦 Lender
    lender = relationship(
        "Lender",
        back_populates="loan_application"
    )

    # 💸 Disbursement
    disbursements = relationship(
        "LoanDisbursement",
        back_populates="loan_application",
        cascade="all, delete-orphan"
    )

    # 📜 Status history
    status_history = relationship(
        "LoanStatusHistory",
        back_populates="loan_application",
        cascade="all, delete-orphan"
    )

    # =====================================================
    # 💳 REPAYMENT
    # =====================================================
    emis = relationship(
        "EMISchedule",
        back_populates="loan",
        cascade="all, delete-orphan"
    )

    payments = relationship(
        "Payment_Transaction",
        back_populates="loan",
        cascade="all, delete-orphan"
    )

    # 🔒 Foreclosure
    foreclosures = relationship(
        "ForeclosureRequest",
        back_populates="loan",
        cascade="all, delete-orphan"
    )

    # 💰 Prepayment
    prepayments = relationship(
        "PrepaymentRequest",
        back_populates="loan",
        cascade="all, delete-orphan"
    )