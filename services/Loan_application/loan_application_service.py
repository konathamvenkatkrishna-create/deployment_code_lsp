from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Profile_KYC.user_profile import UserProfile
from models.Auth.lender import Lender

from core.enums import (
    LoanApplicationStatus,
    LoanApplicationStep,
    enum_value,
    EligibilityStatusEnum,
)

from repositories.Eligibility.eligibility_repository import EligibilityRepository
from core.reference_generator import generate_loan_reference_number
from services.Loan_application.loan_application_validation import validate_final_submission
from services.Loan_application.loan_application_lock_manager_service import ApplicationLockManager

from schemas.Loan_application.loan_application import (
    LoanSubmitResponseSchema,
)

logger = logging.getLogger(__name__)


# =========================================================
# STEP FLOW (CLEAN)
# =========================================================
STEP_FLOW = {
    "LOAN_DETAILS": "PURPOSE",
    "PURPOSE": "REFERENCES",
    "REFERENCES": "DECLARATION",
    "DECLARATION": "SUMMARY",
    "SUMMARY": "SUBMITTED",
}


def get_next_step(current_step: str):
    if not current_step:
        return None
    return STEP_FLOW.get(current_step.upper())


# =========================================================
# GET OR CREATE TRACKER (🔥 FIXED)
# =========================================================
def get_or_create_tracker(db: Session, application: LoanApplication):
    tracker = db.query(LoanApplicationStepTracker).filter(
        LoanApplicationStepTracker.application_id == application.id
    ).first()

    if not tracker:
        tracker = LoanApplicationStepTracker(
            application_id=application.id,
            loan_details_completed=False,
            purpose_completed=False,
            references_completed=False,
            declaration_completed=False,
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),  # ✅ FIXED
            last_completed_step=None
        )
        db.add(tracker)
        db.commit()
        db.refresh(tracker)

    return tracker


# =========================================================
# 🔥 STRICT STEP VALIDATION (FIXED)
# =========================================================
def validate_all_steps_completed(tracker: LoanApplicationStepTracker):

    if not tracker.loan_details_completed:
        raise HTTPException(400, {"pending_step": "LOAN_DETAILS"})

    if not tracker.purpose_completed:
        raise HTTPException(400, {"pending_step": "PURPOSE"})

    if not tracker.references_completed:
        raise HTTPException(400, {"pending_step": "REFERENCES"})

    if not tracker.declaration_completed:
        raise HTTPException(400, {"pending_step": "DECLARATION"})

    if tracker.current_step != enum_value(LoanApplicationStep.SUMMARY):
        raise HTTPException(
            status_code=400,
            detail={"pending_step": "SUMMARY"}
        )


# =========================================================
# SERVICE
# =========================================================
class LoanApplicationService:

    # ---------------------------------------------------
    # ENSURE EDITABLE
    # ---------------------------------------------------
    @staticmethod
    def ensure_editable(application):
        if application.is_submitted:
            raise HTTPException(400, "Application already submitted")

        if application.application_status != enum_value(LoanApplicationStatus.DRAFT):
            raise HTTPException(400, "Application is locked")

    # ---------------------------------------------------
    # GET APPLICATION
    # ---------------------------------------------------
    @staticmethod
    def get_application(db: Session, user_id: int):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No application found for this user")

        tracker = get_or_create_tracker(db, application)

        return {
            "application_id": application.id,
            "application_status": application.application_status,
            "reference_number": application.reference_number,
            "current_step": application.current_step,
            "approved_amount": application.approved_amount,
            "requested_tenure_months": application.requested_tenure_months,
            "interest_rate": application.interest_rate,
            "lender_name": application.lender_name,
            "is_submitted": application.is_submitted,
            "last_completed_step": tracker.last_completed_step
        }

    # ---------------------------------------------------
    # APPLY LOAN
    # ---------------------------------------------------
    @staticmethod
    def apply_loan(db: Session, user_id: int, lender_id: int):

        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(404, "User profile not found")

        eligibility = EligibilityRepository.get_latest_by_user(db, user_id)

        if not eligibility:
            raise HTTPException(400, "Run eligibility check first.")

        if eligibility.eligibility_status == EligibilityStatusEnum.REJECTED:
            raise HTTPException(400, eligibility.failure_reason or "User not eligible")

        existing_draft = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == profile.user_id,
            LoanApplication.is_submitted == False,
            LoanApplication.application_status == enum_value(LoanApplicationStatus.DRAFT)
        ).first()

        if existing_draft:
            return {"message": "Application already in progress."}

        lender = db.query(Lender).filter(Lender.id == lender_id).first()

        if not lender:
            raise HTTPException(404, "Lender not found")

        application = LoanApplication(
            user_profile_id=profile.user_id,
            eligibility_id=eligibility.id,
            approved_amount=float(eligibility.max_eligible_amount),
            lender_id=lender.id,
            lender_name=lender.company_name,
            interest_rate=lender.interest_rate,
            application_status=enum_value(LoanApplicationStatus.DRAFT),
            current_step=enum_value(LoanApplicationStep.LOAN_DETAILS),
            is_submitted=False,
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        get_or_create_tracker(db, application)

        return {"message": "Application created. Proceed step by step."}

    # ---------------------------------------------------
    # SUBMIT APPLICATION (FINAL)
    # ---------------------------------------------------
    @staticmethod
    def submit_latest_application(db: Session, user_id: int, confirm: bool):

        if not confirm:
            raise HTTPException(400, "Confirmation required")

        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(404, "User profile not found")

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.application_status == enum_value(LoanApplicationStatus.DRAFT)
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(400, "No draft application found")

        tracker = get_or_create_tracker(db, application)

        # 🔥 STRICT VALIDATION
        validate_all_steps_completed(tracker)

        validate_final_submission(db, application, tracker)

        application.reference_number = generate_loan_reference_number(db)
        application.application_status = enum_value(LoanApplicationStatus.SUBMITTED)
        application.is_submitted = True
        application.current_step = enum_value(LoanApplicationStep.SUBMITTED)
        application.submitted_at = datetime.now(timezone.utc)

        db.query(LoanApplicationStepTracker).filter(
            LoanApplicationStepTracker.application_id == application.id
        ).update({
            "current_step": enum_value(LoanApplicationStep.SUBMITTED),
            "last_completed_step": enum_value(LoanApplicationStep.SUMMARY)
        })

        ApplicationLockManager.lock_application(application)

        db.commit()
        db.refresh(application)

        return LoanSubmitResponseSchema(
            reference_number=application.reference_number,
            message="Application submitted successfully",
            expected_decision_time="24 hours"
        )