from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db   # ✅ FIXED (use consistent import)
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application_purpose import (
    LoanApplicationPurposeCreate,
    LoanApplicationPurposeResponse,
)

from services.Loan_application.loan_application_purpose_service import (
    LoanApplicationPurposeService,
)


router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Purpose"],
)


# -----------------------------------------------------
# SAVE PURPOSE (USER ONLY)
# -----------------------------------------------------
@router.put(
    "/purpose",
    response_model=LoanApplicationPurposeResponse,
    operation_id="save_loan_purpose"
)
def save_loan_purpose(
    data: LoanApplicationPurposeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    try:
        result = LoanApplicationPurposeService.save_purpose(
            db=db,
            user_id=current_user.id,
            purpose_code=data.purpose_code,
            purpose_description=data.purpose_description,
        )

        # ✅ Cleaner return
        return LoanApplicationPurposeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to save purpose"
        )


# -----------------------------------------------------
# GET PURPOSE (USER ONLY)
# -----------------------------------------------------
@router.get(
    "/purpose",
    response_model=LoanApplicationPurposeResponse,
    operation_id="get_loan_purpose"
)
def get_loan_purpose(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    try:
        result = LoanApplicationPurposeService.get_purpose(
            db=db,
            user_id=current_user.id,
        )

        return LoanApplicationPurposeResponse(
            application_id=result["application_id"],
            purpose_code=result["purpose_code"],
            purpose_description=result["purpose_description"],
            message="Purpose fetched successfully",
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch purpose"
        )