from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.session import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application_declaration import (
    LoanApplicationDeclarationCreate,
    LoanApplicationDeclarationWrapperResponse,  # ✅ FIX
)

from services.Loan_application.loan_application_declaration_service import (
    LoanApplicationDeclarationService
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Loan Application - Declaration"]
)


@router.put(
    "/declaration",
    response_model=LoanApplicationDeclarationWrapperResponse,  # ✅ FIXED
    operation_id="loan_application_submit_declaration"
)
def save_declaration(
    payload: LoanApplicationDeclarationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Step: DECLARATION

    - Saves declaration details
    - Moves to SUMMARY step

    Next Step: SUMMARY
    """

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    return LoanApplicationDeclarationService.save_declaration(
        db=db,
        user_id=current_user.id,
        payload=payload,
        ip_address=client_ip,
        user_agent=user_agent
    )