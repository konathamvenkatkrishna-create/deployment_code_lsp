from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from schemas.Profile_KYC.user_profile_schema import UserRegistrationRequest, UserRegistrationResponse, UserProfileUpdateRequest,UserProfileUpdateResponse
from services.Profile_KYC.registration_service import RegistrationService

router = APIRouter(prefix="/kyc",tags=["User Profile"])

# =====================================================
# CREATE PROFILE (USER ONLY)
# =====================================================
@router.post( "/profile", response_model=UserRegistrationResponse, status_code=201)
def create_user_profile( request: UserRegistrationRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles("USER"))):
    result = RegistrationService.create_profile( db, current_user.id, request)

    return {
        "user_id": result.user_id,
        "message": "Profile created successfully. Proceed to PAN verification.",
        "pan_status": result.pan_status,
        "aadhaar_status": result.aadhaar_status,
        "bank_status": result.bank_status,
        "document_status": result.document_status,
        "kyc_status": result.kyc_status,
        "next_step": "Verify your PAN",
    }


# =====================================================
# GET PROFILE (USER ONLY)
# =====================================================
@router.get("/profile")
def get_user_profile( db: Session = Depends(get_db), current_user: User = Depends(require_roles("USER"))):
    try:
        profile = RegistrationService.get_profile( db, current_user.id)

        return {
            "user_id": profile.user_id,
            "email": profile.email,
            "full_name": profile.full_name,
            "dob": profile.dob.isoformat(),
            "permanent_address": profile.permanent_address,
            "temporary_address": profile.temporary_address,
            "employment_type": profile.employment_type,
            "monthly_income": float(profile.monthly_income),
            "aadhaar_number": profile.aadhaar_number,
            "pan_number": profile.pan_number,
            "pan_status": profile.pan_status,
            "aadhaar_status": profile.aadhaar_status,
            "bank_status": profile.bank_status,
            "document_status": profile.document_status,
            "kyc_status": profile.kyc_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException( status_code=500, detail="Failed to fetch user profile")

# =====================================================
# UPDATE PROFILE (USER ONLY)
# =====================================================
@router.put("/profile", response_model=UserProfileUpdateResponse)
def update_user_profile(
    request: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        result = RegistrationService.update_profile( db, current_user.id, request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException( status_code=500, detail="Failed to update profile")