from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application import (
    LoanSubmitRequestSchema,
    LoanSubmitResponseSchema,
)

from services.Loan_application.loan_application_service import (
    LoanApplicationService,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application Submit "],
)


# -----------------------------------------------------
# Current User Dependency
# -----------------------------------------------------
def get_current_user(
    current_user: User = Depends(require_roles("USER")),
) -> User:
    return current_user


@router.post(
    "/submit",
    response_model=LoanSubmitResponseSchema,
)
def submit(
    data: LoanSubmitRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return LoanApplicationService.submit_latest_application(
        db=db,
        user_id=current_user.id,
        confirm=data.confirm,
    )
