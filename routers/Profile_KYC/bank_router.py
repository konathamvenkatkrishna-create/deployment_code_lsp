from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from schemas.Profile_KYC.bank_schema import BankVerificationRequest, BankUpdateRequest, BankVerificationResponse
from services.Profile_KYC.bank_verification_service import BankVerificationService
from repositories.Profile_KYC.kyc_bank_verification_repository import KYCBankVerificationRepository

router = APIRouter(prefix="/kyc", tags=["Bank Verification"])


# ============================================================
# SAVE BANK DETAILS
# ============================================================
@router.post("/bank_details", response_model=BankVerificationResponse)
def save_bank_details(
    request: BankVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    BankVerificationService.save_bank_details(
        db,
        profile,
        request.account_number,
        request.account_holder_name,
        request.bank_name,
        request.ifsc,
    )

    return BankVerificationResponse(
        message="Bank details saved successfully",
        next="Proceed to bank verification",
    )


# ============================================================
# UPDATE BANK DETAILS
# ============================================================
@router.put("/bank_details", response_model=BankVerificationResponse)
def update_bank_details(
    request: BankUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    payload = request.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided to update",
        )

    BankVerificationService.update_bank_details(
        db,
        profile,
        request.account_number,
        request.account_holder_name,
        request.bank_name,
        request.ifsc,
    )

    return BankVerificationResponse(
        message="Bank details updated successfully",
        next="Proceed to bank verification",
    )


# ============================================================
# VERIFY BANK
# ============================================================
@router.post("/bank_verify", response_model=BankVerificationResponse)
def verify_bank(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    # Optional strict check (recommended)
    if profile.pan_status != "VERIFIED" or profile.aadhaar_status != "VERIFIED":
        raise HTTPException(
            400,
            "Complete PAN + Aadhaar verification first",
        )

    latest = KYCBankVerificationRepository.get_latest_by_user_id(
        db, profile.user_id
    )

    if not latest:
        raise HTTPException(
            400,
            "Bank details not found. Please add bank details first",
        )

    if latest.status == "VERIFIED":
        return BankVerificationResponse(
            message="Bank already verified",
            next="Upload documents",
        )

    result = BankVerificationService.verify_bank_account(
        db,
        profile,
        latest.account_number,
        latest.account_holder_name,
        latest.bank_name,
        latest.ifsc,
    )

    return BankVerificationResponse(
        message=result["message"],
        next="Upload required documents for final KYC",
    )