from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.Loan_application.loan_application_references import LoanApplicationReference
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Loan_application.loan_application import LoanApplication

from core.enums import LoanApplicationStatus, enum_value


def validate_final_submission(
    db: Session,
    application: LoanApplication,
    tracker: LoanApplicationStepTracker
):

    # =====================================================
    # 1️⃣ Check application is still draft (ENUM SAFE)
    # =====================================================
    if application.application_status != enum_value(LoanApplicationStatus.DRAFT):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application already submitted"
        )

    # =====================================================
    # 2️⃣ Validate steps completion
    # =====================================================
    if not tracker.loan_details_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": "LOAN_DETAILS",
                "message": "Loan details not completed"
            }
        )

    if not tracker.purpose_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": "PURPOSE",
                "message": "Loan purpose not completed"
            }
        )

    if not tracker.references_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": "REFERENCES",
                "message": "References not completed"
            }
        )

    if not tracker.declaration_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": "DECLARATION",
                "message": "Declaration not completed"
            }
        )

    # =====================================================
    # 3️⃣ Validate user reached SUMMARY step
    # =====================================================
    if tracker.current_step != "SUMMARY":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "pending_step": "SUMMARY",
                "message": "Please review application before submission"
            }
        )

    # =====================================================
    # 4️⃣ Validate references count
    # =====================================================
    references = (
        db.query(LoanApplicationReference)
        .filter(LoanApplicationReference.application_id == application.id)
        .all()
    )

    if len(references) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly 2 references are required"
        )

    # =====================================================
    # 5️⃣ Validate references verification
    # =====================================================
    if not all(ref.is_verified for ref in references):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All references must be OTP verified"
        )

    # =====================================================
    # ✅ FINAL SUCCESS
    # =====================================================
    return True