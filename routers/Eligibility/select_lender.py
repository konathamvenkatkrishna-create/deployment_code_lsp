from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.dependencies import get_current_user

from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from models.Eligibility.loan_eligibility import LoanEligibility
from models.Auth.lender import Lender
from models.Loan_application.loan_application import LoanApplication

from core.enums import LoanApplicationStatus


router = APIRouter(prefix="/lenders", tags=["Lenders"])


class SelectLenderRequest(BaseModel):
    lender_id: int
    tenure_months: int


@router.post("/select")
def select_lender(
    request: SelectLenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    eligibility = db.query(LoanEligibility).filter(
        LoanEligibility.user_id == user_id
    ).first()

    if not eligibility or (eligibility.eligibility_status or "").upper() != "ELIGIBLE":
        raise HTTPException(status_code=400, detail="User is not eligible")

    lender = db.query(Lender).filter(
        Lender.id == request.lender_id
    ).first()

    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")

    if lender.max_amount < eligibility.max_eligible_amount:
        raise HTTPException(
            status_code=400,
            detail="Lender does not support this loan amount"
        )

    allowed_tenures = [3, 6, 9, 12]
    if request.tenure_months not in allowed_tenures:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tenure. Allowed values: {allowed_tenures}"
        )

    existing_app = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == profile.user_id,
        LoanApplication.application_status == LoanApplicationStatus.DRAFT
    ).first()

    if existing_app:
        return {
            "message": "Draft already exists",
            "application_id": existing_app.id,
        }

    application = LoanApplication(
        user_profile_id=profile.user_id,        
        eligibility_id=eligibility.id,
        lender_id=lender.id,
        lender_name=lender.company_name,            
        interest_rate=lender.interest_rate,
        approved_amount=eligibility.max_eligible_amount,
        requested_tenure_months=request.tenure_months,
        application_status=LoanApplicationStatus.DRAFT,
        current_step="LENDER_SELECTED",
        is_submitted=False,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "message": "Lender selected successfully",
        "application_id": application.id,
        "lender_id": lender.id,
        "lender_name": lender.company_name,  # ✅ derive here
        "interest_rate": float(lender.interest_rate),
        "approved_amount": float(eligibility.max_eligible_amount),
        "tenure_months": application.requested_tenure_months,
        "status": application.application_status,
    }