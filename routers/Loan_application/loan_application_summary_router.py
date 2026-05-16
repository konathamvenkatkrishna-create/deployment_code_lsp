from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Loan_application.loan_application_summary_service import (
    LoanApplicationSummaryService,
)
from schemas.Loan_application.loan_application_summary import (
    LoanApplicationSummaryResponseSchema,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Summary"],
)


@router.get(
    "/summary",
    response_model=LoanApplicationSummaryResponseSchema,
    responses={
        400: {
            "description": "Pending steps not completed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "pending_step": "DECLARATION"
                        }
                    }
                }
            },
        },
        404: {
            "description": "No loan application found"
        }
    }
)
def get_application_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Loan Application Summary

    ✅ Conditions:
    - Lender must already be selected
    - Interest rate must be available
    - Tenure must be selected
    - All steps must be completed

    ❌ If any step missing:
        → returns { "pending_step": "<STEP_NAME>" }

    📌 Summary includes:
    - User details
    - Loan details (amount, EMI, interest, lender)
    - Charges
    - References
    - Final submission readiness

    ⚠️ Works for:
    - Draft applications
    - Submitted applications
    """
    return LoanApplicationSummaryService.get_summary_by_user(
        db=db,
        user_id=current_user.id
    )