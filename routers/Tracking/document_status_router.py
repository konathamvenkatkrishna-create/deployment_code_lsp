# routers/document_status_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication

from repositories.Tracking.loan_application_repo import LoanApplicationRepository
from services.Tracking.document_status_service import DocumentStatusService


router = APIRouter(
    prefix="/applications",
    tags=["Application Tracking"]
)


# ------------------------------------------------
# DOCUMENT STATUS (SECURE)
# ------------------------------------------------
@router.get("/{application_id}/document-status")
def get_document_status(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    """
    Get document status + rejection reasons for UI
    """

    try:
        logger.info(f"[DOC STATUS REQUEST] user={current_user.id}, app={application_id}")

        # 🔍 Fetch application with profile
        application = db.query(LoanApplication).options(
            joinedload(LoanApplication.user_profile)
        ).filter(
            LoanApplication.id == application_id
        ).first()

        if not application:
            raise HTTPException(404, "Application not found")

        # 🔐 USER → only own application
        if current_user.role == "USER":
            if not application.user_profile or application.user_profile.user_id != current_user.id:
                logger.warning(
                    f"[DOC ACCESS DENIED] user={current_user.id}, app={application_id}"
                )
                raise HTTPException(403, "Access denied")

        # 🔥 Get document status
        result = DocumentStatusService.get_document_status(db, application)

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"[DOC STATUS ERROR] user={current_user.id}, app={application_id}, error={str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch document status"
        )