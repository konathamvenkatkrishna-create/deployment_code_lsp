from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker

from core.enums import LoanApplicationStep

from services.Eligibility.loan_service import LoanCalculationService

router = APIRouter(
    prefix="/loan",
    tags=["Loan Calculator"]
)


# =====================================================
# GET LOAN CALCULATION
# =====================================================
@router.get("/result/me", operation_id="get_loan_calculation")
def get_loan_calculation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    try:
        logger.info(f"[GET EMI RESULT] user={current_user.id}")

        record = LoanCalculationService.get_calculation(
            db=db,
            user_id=current_user.id
        )

        if not record:
            raise HTTPException(
                status_code=404,
                detail="No EMI calculation found. Please calculate EMI first."
            )

        # =====================================================
        # 🔥 ENSURE STEP IS UPDATED (IMPORTANT FIX)
        # =====================================================
        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == current_user.id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if application:
            application.current_step = LoanApplicationStep.EMI_CALCULATED.value

            tracker = db.query(LoanApplicationStepTracker).filter(
                LoanApplicationStepTracker.application_id == application.id
            ).first()

            if tracker:
                tracker.current_step = LoanApplicationStep.EMI_CALCULATED.value

            db.commit()

        # =====================================================
        return {
            "status": "success",
            "data": {
                "id": record.id,
                "requested_amount": record.requested_amount,
                "eligible_amount": record.eligible_amount,
                "tenure_months": record.tenure_months,
                "interest_rate_pa": record.interest_rate_pa,
                "monthly_emi": record.monthly_emi,
                "total_repayment": record.total_repayment,
                "total_interest": record.total_interest,
                "status": record.status,
            },
            "next_step": "PURPOSE_SELECTION"   # 🔥 FLOW GUIDE
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[EMI RESULT ERROR] user={current_user.id}, error={str(e)}")
        raise HTTPException(500, "Failed to fetch EMI result")