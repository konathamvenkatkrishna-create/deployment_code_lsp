from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.database import get_db
from core.dependencies import get_current_user

from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from models.Eligibility.loan_eligibility import LoanEligibility
from models.Eligibility.credit_profile import CreditProfile
from models.Auth.lender import Lender


router = APIRouter(prefix="/lenders", tags=["Lenders"])


@router.get("/")
def get_lenders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    role = (current_user.role or "").upper()

    if role == "SUPER_ADMIN":
        lenders = db.query(Lender).all()

        return {
            "role": "SUPER_ADMIN",
            "total_lenders": len(lenders),
            "lenders": [
                {
                    "id": l.id,
                    "name": l.company_name,
                    "interest_rate": float(l.interest_rate or 0),
                    "max_amount": float(l.max_amount or 0),
                    "min_credit_score": l.min_credit_score,
                }
                for l in lenders
            ],
        }

    elif role == "USER":
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(404, "User profile not found")
        eligibility = db.query(LoanEligibility).filter(
            LoanEligibility.user_id == user_id
        ).first()

        if not eligibility:
            raise HTTPException(400, "Eligibility not found")

        if (eligibility.eligibility_status or "").upper() != "ELIGIBLE":
            return {"message": "User not eligible", "lenders": []}
        credit_profile = (
            db.query(CreditProfile)
            .filter(CreditProfile.user_id == user_id)
            .order_by(
                CreditProfile.pulled_at.desc(),
                CreditProfile.id.desc()
            )
            .first()
        )

        if not credit_profile:
            raise HTTPException(404, "Credit profile not found")
        lenders = db.query(Lender).filter(
            Lender.max_amount >= eligibility.max_eligible_amount,
            or_(
                Lender.min_credit_score == None,  # accepts all users
                Lender.min_credit_score <= credit_profile.credit_score
            )
        ).order_by(Lender.interest_rate.asc()).all()  # optional sorting
        
        if not lenders:
            return {
                "role": "USER",
                "user_id": user_id,
                "message": "Lenders are not available",
            }

        return {
            "role": "USER",
            "user_id": user_id,
            "credit_score": credit_profile.credit_score,
            "approved_amount": float(eligibility.max_eligible_amount),
            "lenders": [
                {
                    "id": l.id,
                    "name": l.company_name,
                    "interest_rate": float(l.interest_rate or 0),
                    "max_amount": float(l.max_amount or 0),
                    "min_credit_score": l.min_credit_score,
                }
                for l in lenders
            ],
        }
    else:
        raise HTTPException(403, "Unauthorized role")