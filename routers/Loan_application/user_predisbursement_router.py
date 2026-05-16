from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from services.Loan_application.pre_disbursement_service import PreDisbursementService
from schemas.Loan_application.loan_predisbursement_schema import (
    PreDisbursementResponseSchema
)


router = APIRouter(
    prefix="/user/disbursement",
    tags=["User PreDisbursement"]
)


# =====================================================
# 👤 USER PRE-DISBURSEMENT PREVIEW (NO APPLICATION ID)
# =====================================================
@router.get(
    "/me",
    response_model=PreDisbursementResponseSchema,
    status_code=status.HTTP_200_OK
)
def preview_user_disbursement(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    User can view their loan charges before disbursement

    - No application_id required
    - Fetches latest application automatically
    """

    try:
        return PreDisbursementService.get_preview_for_user(
            db=db,
            user_id=current_user.id
        )

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Preview failed: {str(e)}"
        )