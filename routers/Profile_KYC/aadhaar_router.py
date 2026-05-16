from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from services.Profile_KYC.aadhaar_verification_service import AadhaarVerificationService
from schemas.Profile_KYC.aadhaar_schema import AadhaarVerificationRequest, AadhaarVerificationResponse


router = APIRouter(prefix="/kyc",tags=["Aadhaar Verification"])

@router.post("/aadhaar_verify", response_model=AadhaarVerificationResponse)
def verify_aadhaar( db: Session = Depends(get_db), current_user: User = Depends(require_roles("USER"))):
    try:
        result = AadhaarVerificationService.verify_aadhaar( db=db, user_id=current_user.id)
        return AadhaarVerificationResponse(**result)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Aadhaar verification service temporarily unavailable"
        )