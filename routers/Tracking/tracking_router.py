from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from services.Tracking.tracking_service import TrackingService

from schemas.Tracking.loan_status_schema import LoanStatusResponse
from schemas.Tracking.loan_timeline_schema import LoanStatusHistoryItem
from schemas.Loan_application.loan_application import LoanApplicationResponseSchema

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication


router = APIRouter(
    prefix="/loan",
    tags=["Loan Tracking"]
)


# ------------------------------------------------
# COMMON FUNCTION (OWNERSHIP CHECK)
# ------------------------------------------------
def validate_application_access(db: Session, application_id: int, current_user: User):
    application = db.query(LoanApplication).options(
        joinedload(LoanApplication.user_profile)
    ).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(404, "Application not found")

    # 🔐 USER restriction
    if current_user.role == "USER":
        if not application.user_profile or application.user_profile.user_id != current_user.id:
            logger.warning(
                f"[ACCESS DENIED] user={current_user.id}, app={application_id}"
            )
            raise HTTPException(403, "Access denied")

    return application




# ------------------------------------------------
# GET APPLICATION STATUS
# ------------------------------------------------
@router.get(
    "/application/{application_id}/status",
    response_model=LoanStatusResponse,
    operation_id="get_application_status"
)
def get_application_status(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    try:
        application = validate_application_access(db, application_id, current_user)

        return TrackingService.get_application_status(
            db=db,
            application_id=application.id,
            user_id=current_user.id
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"[STATUS ERROR] user={current_user.id}, app={application_id}, error={str(e)}"
        )
        raise HTTPException(500, "Failed to fetch status")


# ------------------------------------------------
# GET APPLICATION TIMELINE
# ------------------------------------------------
@router.get(
    "/application/{application_id}/timeline",
    response_model=list[LoanStatusHistoryItem],
    operation_id="get_application_timeline"
)
def get_application_timeline(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    try:
        application = validate_application_access(db, application_id, current_user)

        return TrackingService.get_application_timeline(
            db=db,
            application_id=application.id,
            user_id=current_user.id
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"[TIMELINE ERROR] user={current_user.id}, app={application_id}, error={str(e)}"
        )
        raise HTTPException(500, "Failed to fetch timeline")