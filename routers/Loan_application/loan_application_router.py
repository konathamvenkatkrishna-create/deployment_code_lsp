from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application import (
    LoanSubmitRequestSchema,
    LoanSubmitResponseSchema,
    LoanApplicationResponseSchema,
)

from services.Loan_application.loan_application_service import (
    LoanApplicationService,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Apply Loan Application"],
)


# -----------------------------------------------------
# Current User Dependency
# -----------------------------------------------------
def get_current_user(
    current_user: User = Depends(require_roles("USER")),
) -> User:
    return current_user


# =====================================================
# APPLY LOAN
# =====================================================
@router.post("/apply")
def apply(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return LoanApplicationService.apply_loan(
        db=db,
        user_id=current_user.id,
    )


# =====================================================
# ✅ GET CURRENT USER APPLICATION (UPDATED)
# =====================================================
@router.get(
    "/me",
    response_model=LoanApplicationResponseSchema,
)
def get_my_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return LoanApplicationService.get_application(
        db=db,
        user_id=current_user.id,
    )


# =====================================================
# SUBMIT APPLICATION
# =====================================================
@router.post(
    "/submit",
    response_model=LoanSubmitResponseSchema,
)
def submit_application(
    payload: LoanSubmitRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return LoanApplicationService.submit_latest_application(
        db=db,
        user_id=current_user.id,
        confirm=payload.confirm,
    )