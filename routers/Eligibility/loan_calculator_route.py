from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from core.database import get_db
from core.dependencies import get_current_user

from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Eligibility.loan_eligibility import LoanEligibility
from models.Auth.lender import Lender

from core.enums import LoanApplicationStatus, LoanApplicationStep
from core.Loan_calculator import calculate_loan_summary


router = APIRouter(
    prefix="/loan",
    tags=["Loan Calculator"]
)


@router.get("/calculate")
def calculate_emi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    # =====================================================
    # USER PROFILE
    # =====================================================
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(404, "Profile not found")

    # =====================================================
    # APPLICATION
    # =====================================================
    application = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == profile.user_id,
        LoanApplication.application_status == LoanApplicationStatus.DRAFT
    ).order_by(LoanApplication.id.desc()).first()

    if not application:
        raise HTTPException(404, "No draft application found")

    if not application.requested_tenure_months:
        raise HTTPException(400, "Tenure not selected")

    if not application.lender_id:
        raise HTTPException(400, "Lender not selected")

    # =====================================================
    # LENDER
    # =====================================================
    lender = db.query(Lender).filter(
        Lender.id == application.lender_id
    ).first()

    if not lender or not lender.interest_rate:
        raise HTTPException(400, "Invalid lender configuration")

    # =====================================================
    # ELIGIBILITY
    # =====================================================
    eligibility = db.query(LoanEligibility).filter(
        LoanEligibility.user_id == user_id
    ).first()

    if not eligibility or (eligibility.eligibility_status or "").upper() != "ELIGIBLE":
        raise HTTPException(400, "User not eligible")

    principal = Decimal(eligibility.max_eligible_amount)

    # =====================================================
    # CALCULATION
    # =====================================================
    result = calculate_loan_summary(
        principal=principal,
        interest_rate=lender.interest_rate,
        tenure_months=application.requested_tenure_months,
        first_emi_date=date.today()
    )

    # =====================================================
    # UPDATE APPLICATION
    # =====================================================
    application.monthly_emi = result.get("emi")
    application.total_repayment = result.get("total_amount")
    application.processing_fee = result.get("processing_fee")
    application.gst_amount = result.get("gst_amount")
    application.approved_amount = principal
    application.interest_rate = lender.interest_rate

    # =====================================================
    # 🔥 TRACKER UPDATE (CORRECTED FLOW)
    # =====================================================
    tracker = db.query(LoanApplicationStepTracker).filter(
        LoanApplicationStepTracker.application_id == application.id
    ).first()

    if not tracker:
        tracker = LoanApplicationStepTracker(
            application_id=application.id
        )
        db.add(tracker)

    # ✅ Mark EMI step completed
    tracker.loan_details_completed = True

    # ✅ Move to EMI_CALCULATED (not directly PURPOSE)
    tracker.current_step = LoanApplicationStep.EMI_CALCULATED.value
    application.current_step = LoanApplicationStep.EMI_CALCULATED.value

    # =====================================================
    db.commit()
    db.refresh(application)

    return {
        "status": "success",
        "data": {
            "application_id": application.id,
            "user_id": user_id,
            "loan_amount": principal,
            "interest_rate": Decimal(lender.interest_rate),
            "tenure_months": application.requested_tenure_months,
            "monthly_emi": application.monthly_emi,
            "total_repayment": application.total_repayment,
            "processing_fee": application.processing_fee,
            "gst_amount": application.gst_amount,
            "total_interest": float(round(
                application.total_repayment - principal, 2
            )),
            "amortization_schedule": result.get("schedule"),
        },
        "next_step": "PURPOSE"
    }