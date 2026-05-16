from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_roles

from repositories.Eligibility.credit_repository import CreditRepository
from models.Eligibility.credit_profile import CreditProfile
from models.Auth.user import User


router = APIRouter(
    prefix="/credit",
    tags=["Credit Profile"]
)

@router.post("/generate")
def generate_credit_profile(
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER")),
):
    user_id = current_user.id

    try:
        profile: CreditProfile = CreditRepository.create_dummy_credit_profile(
            db=db,
            user_id=user_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate credit profile: {str(e)}"
        )

    return {
        "message": "Credit profile fetched successfully" if not force_refresh else "Credit profile refreshed successfully",
        "credit_profile_id": profile.id,
        "credit_score": profile.credit_score,
        "bureau_name": profile.bureau_name,
        "total_active_loans": profile.total_active_loans,
        "total_existing_emi": float(profile.total_existing_emi or 0),
    }

@router.get("/me")
def get_my_credit_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    profile = CreditRepository.get_latest_credit_profile(db, current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit profile not found. Generate one first."
        )

    return {
        "credit_profile_id": profile.id,
        "credit_score": profile.credit_score,
        "bureau_name": profile.bureau_name,
        "total_active_loans": profile.total_active_loans,
        "total_existing_emi": float(profile.total_existing_emi or 0)
    }