from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.logger import logger
from core.dependencies import require_roles

from services.Tracking.status_update_service import StatusUpdateService

from schemas.Tracking.internal_status_schema import (
    InternalStatusUpdateRequest,
    InternalStatusUpdateResponse
)

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication


router = APIRouter(
    prefix="/internal",
    tags=["Internal Module APIs"]
)


# ------------------------------------------------
# STATUS UPDATE (ADMIN ONLY)
# ------------------------------------------------
@router.post(
    "/status/update",
    response_model=InternalStatusUpdateResponse,
    operation_id="internal_status_update"
)
def update_internal_status(
    request: InternalStatusUpdateRequest,
    http_request: Request,
    db: Session = Depends(get_db),

    # 🔐 STRICT ACCESS CONTROL
    current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
):
    try:
        # ------------------------------------------------
        # VALIDATE TOKEN (OPTIONAL BUT SAFE)
        # ------------------------------------------------
        authorization = http_request.headers.get("Authorization")

        if not authorization:
            logger.warning(f"[MISSING TOKEN] user={current_user.id}")
            raise HTTPException(401, "Missing Authorization header")

        # ------------------------------------------------
        # FETCH EXISTING APPLICATION (FOR AUDIT)
        # ------------------------------------------------
        existing_app = db.query(LoanApplication).filter(
            LoanApplication.id == request.application_id
        ).first()

        if not existing_app:
            raise HTTPException(404, "Application not found")

        old_status = (
            existing_app.application_status.value
            if existing_app.application_status else None
        )

        # ------------------------------------------------
        # LOG REQUEST
        # ------------------------------------------------
        logger.info(
            f"[STATUS UPDATE REQUEST] user={current_user.id}, "
            f"app={request.application_id}, old={old_status}, new={request.status}"
        )

        # ------------------------------------------------
        # CLEAN COMMENT
        # ------------------------------------------------
        comment = request.comment.strip() if request.comment else None

        # ------------------------------------------------
        # UPDATE STATUS
        # ------------------------------------------------
        updated_app = StatusUpdateService.update_status(
            db=db,
            application_id=request.application_id,
            user_id=current_user.id,
            new_status=request.status,
            source=current_user.role,
            comment=comment,
            token=authorization
        )

        # ------------------------------------------------
        # LOG SUCCESS (AUDIT)
        # ------------------------------------------------
        logger.info(
            f"[STATUS UPDATED] user={current_user.id}, "
            f"app={updated_app.id}, from={old_status}, to={updated_app.application_status}"
        )

        return {
            "success": True,
            "application_id": updated_app.id,
            "old_status": old_status,
            "new_status": (
                updated_app.application_status.value
                if updated_app.application_status else None
            ),
            "message": "Status updated successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"[STATUS UPDATE ERROR] user={current_user.id}, "
            f"app={request.application_id}, error={str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to update status"
        )