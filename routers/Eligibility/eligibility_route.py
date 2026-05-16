from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User

from services.Eligibility.eligibility_service import (
    EligibilityService,
    CREDIT_SCORE_TIERS
)

from services.Loan_application.loan_application_service import LoanApplicationService

router = APIRouter(
    prefix="/eligibility",
    tags=["Loan Eligibility"]
)


@router.post("/check", operation_id="check_loan_eligibility")
def check_loan_eligibility(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Checks loan eligibility and prepares user for EMI calculation flow.
    """

    try:
        logger.info(f"[ELIGIBILITY CHECK] user={current_user.id}")

        # =====================================================
        # 🔥 ENSURE APPLICATION EXISTS (IMPORTANT FIX)
        # =====================================================
        application = LoanApplicationService.get_application(db, current_user.id)

        if not application:
            logger.info(f"[AUTO APPLY] creating application for user={current_user.id}")
            application = LoanApplicationService.apply_loan(
                db=db,
                user_id=current_user.id
            )

        # =====================================================
        # CHECK ELIGIBILITY
        # =====================================================
        eligibility = EligibilityService.check_eligibility(
            db=db,
            user=current_user
        )

    except ValueError as e:
        logger.warning(f"[ELIGIBILITY ERROR] user={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"[ELIGIBILITY FAILED] user={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail="Eligibility check failed")

    status = eligibility.eligibility_status

    # =====================================================
    # REJECTED RESPONSE
    # =====================================================
    if status == "REJECTED":
        return {
            "user_id": current_user.id,
            "eligibility_status": status,
            "failure_reason": eligibility.failure_reason,
            "credit_summary": {
                "current_score": eligibility.credit_score_used,
                "bureau": eligibility.bureau_name,
            },
            "credit_score_tiers": [
                {
                    "min_score": score,
                    "max_loan_amount": amount
                }
                for score, amount in CREDIT_SCORE_TIERS
            ],
            "message": "You are not eligible for a loan."
        }

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================
    approved_amount = float(eligibility.max_eligible_amount or 0)

    return {
        "user_id": current_user.id,
        "eligibility_status": status,
        "loan_offer": {
            "approved_amount": approved_amount,
        },
        "credit_summary": {
            "current_score": eligibility.credit_score_used,
            "bureau": eligibility.bureau_name,
        },
        "next_step": "EMI_CALCULATION",   # 🔥 IMPORTANT FOR FLOW
        "message": "You are eligible. Proceed to EMI calculation."
    }