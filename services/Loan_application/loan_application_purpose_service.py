from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_purpose import LoanApplicationPurpose
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from repositories.Loan_application.loan_application_purpose_repo import (
    LoanApplicationPurposeRepository,
)

from core.enums import LoanApplicationStep

from services.Loan_application.loan_application_service import (
    LoanApplicationService,
    get_next_step,
)


# =====================================================
# COMMON HELPER
# =====================================================
def normalize_step(step: str | None) -> str:
    """Normalize DB step value"""
    return (step or "").strip().upper()


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
            current_step=LoanApplicationStep.EMI_CALCULATED.value,
            last_completed_step=None
        )
        db.add(tracker)
        db.commit()
        db.refresh(tracker)

    return tracker


class LoanApplicationPurposeService:

    # -----------------------------------------------------
    # SAVE PURPOSE
    # -----------------------------------------------------
    @staticmethod
    def save_purpose(
        db: Session,
        user_id: int,
        purpose_code,
        purpose_description: str | None,
    ):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active draft application found"
            )

        LoanApplicationService.ensure_editable(application)

        tracker = get_or_create_tracker(db, application)

        # =====================================================
        # 🔥 STEP VALIDATION (FIXED PROPERLY)
        # =====================================================
        current_step = normalize_step(tracker.current_step)
        expected_step = LoanApplicationStep.EMI_CALCULATED.value

        if current_step != expected_step:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid step. Expected {expected_step}, got {current_step}"
            )

        # 🚫 BLOCK if already completed
        if tracker.purpose_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purpose already completed"
            )

        # =====================================================
        # CREATE PURPOSE
        # =====================================================
        purpose = LoanApplicationPurpose(
            application_id=application.id,
            purpose_code=purpose_code,
            purpose_description=purpose_description
        )

        purpose = LoanApplicationPurposeRepository.create(db, purpose)

        # =====================================================
        # UPDATE TRACKER
        # =====================================================
        tracker.purpose_completed = True
        tracker.last_completed_step = LoanApplicationStep.PURPOSE.value

        next_step = get_next_step(tracker.current_step)

        if next_step:
            tracker.current_step = next_step
            application.current_step = next_step

        db.commit()
        db.refresh(purpose)
        db.refresh(tracker)

        return {
            "application_id": application.id,
            "purpose_code": purpose.purpose_code,
            "purpose_description": purpose.purpose_description,
            "current_step": tracker.current_step,
            "next_step": get_next_step(tracker.current_step),
            "message": "Purpose saved successfully"
        }

    # -----------------------------------------------------
    # GET PURPOSE
    # -----------------------------------------------------
    @staticmethod
    def get_purpose(
        db: Session,
        user_id: int,
    ):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No application found"
            )

        purpose = LoanApplicationPurposeRepository.get_by_application_id(
            db, application.id
        )

        return {
            "application_id": application.id,
            "purpose_code": purpose.purpose_code if purpose else None,
            "purpose_description": purpose.purpose_description if purpose else None,
            "is_purpose_completed": purpose is not None,
            "current_step": application.current_step
        }