from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Literal

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User
from models.Auth.lender import Lender
from models.Loan_application.loan_application import LoanApplication

from services.Loan_application.lender_service import LenderService
from services.Loan_application.loan_disbursement_service import LoanDisbursementService
from services.Loan_application.pre_disbursement_service import PreDisbursementService

from schemas.Loan_application.lender import LenderApplicationListResponse
from schemas.Loan_application.loan_disbursement_schema import (
    DisbursementRequestSchema,
    DisbursementResponseSchema
)
from schemas.Loan_application.loan_predisbursement_schema import (
    PreDisbursementResponseSchema
)
from schemas.Loan_application.rejection_schema import RejectRequestSchema


router = APIRouter(
    prefix="/lender-dashboard",
    tags=["Lender Dashboard"]
)


# -----------------------------------------------------
# 🔐 VALIDATE LENDER ACCESS
# -----------------------------------------------------
def validate_lender_access(db: Session, application_id: int, user_id: int):

    lender = db.query(Lender).filter(
        Lender.user_id == user_id
    ).first()

    if not lender:
        raise HTTPException(404, "Lender not found")

    application = db.query(LoanApplication).options(
        joinedload(LoanApplication.user_profile)
    ).filter(
        LoanApplication.id == application_id
    ).first()

    if not application:
        raise HTTPException(404, "Application not found")

    if application.lender_id != lender.id:
        logger.warning(
            f"[UNAUTHORIZED ACCESS] user={user_id}, lender={lender.id}, app_lender={application.lender_id}"
        )
        raise HTTPException(403, "Access denied")

    return application


# =====================================================
# VIEW APPLICATIONS
# =====================================================
@router.get(
    "/my-applications",
    response_model=List[LenderApplicationListResponse]
)
def view_lender_applications(
    status: Optional[Literal["SUBMITTED", "APPROVED", "REJECTED"]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        applications = LenderService.get_lender_applications(
            db=db,
            user_id=current_user.id,
            status=status
        )

        return [
            LenderApplicationListResponse(
                application_id=app.id,
                reference_number=app.reference_number,
                approved_amount=app.approved_amount,
                tenure_months=app.requested_tenure_months,
                application_status=app.application_status,
                submitted_at=app.submitted_at
            )
            for app in applications
        ]

    except Exception as e:
        logger.error(f"[VIEW ERROR] lender={current_user.id}, error={str(e)}")
        raise HTTPException(500, "Failed to fetch applications")


# =====================================================
# APPROVE
# =====================================================
@router.post("/approve/{application_id}")
def approve_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return LenderService.approve_application(
            db,
            application_id,
            current_user.id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[APPROVE ERROR] {str(e)}")
        raise HTTPException(400, "Approval failed")


# =====================================================
# REJECT
# =====================================================
@router.post("/reject/{application_id}")
def reject_application(
    application_id: int,
    request: RejectRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return LenderService.reject_application(
            db,
            application_id,
            current_user.id,
            request.rejection_reason
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[REJECT ERROR] {str(e)}")
        raise HTTPException(400, "Rejection failed")


# =====================================================
# PREVIEW
# =====================================================
@router.get(
    "/disbursement/preview/{application_id}",
    response_model=PreDisbursementResponseSchema
)
def preview_pre_disbursement_lender(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        validate_lender_access(db, application_id, current_user.id)

        return PreDisbursementService.get_preview(
            db=db,
            application_id=application_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PREVIEW ERROR] {str(e)}")
        raise HTTPException(400, "Preview failed")


# =====================================================
# DISBURSE (UPDATED FLOW)
# =====================================================
@router.post(
    "/disbursement/{application_id}",
    response_model=DisbursementResponseSchema
)
def disburse_loan(
    application_id: int,
    request: DisbursementRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("LENDER")),
):
    try:
        application = validate_lender_access(db, application_id, current_user.id)

        response = LoanDisbursementService.disburse_loan(
            db=db,
            application_id=application_id,
            payment_mode=request.payment_mode,
            background_tasks=background_tasks
        )

        # ✅ Return clean status for UI
        return {
            "application_id": response["application_id"],
            "payout_id": response["payout_id"],
            "payout_status": response["payout_status"],
            "application_status": response["application_status"],
            "message": "Disbursement initiated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DISBURSE ERROR] {str(e)}")
        raise HTTPException(400, "Disbursement failed")