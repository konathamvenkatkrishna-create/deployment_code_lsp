from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.session import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from schemas.Loan_application.loan_application_references_otp import (
    ReferenceOTPSendRequest,
    ReferenceOTPVerifyRequest,
    ReferenceOTPVerifyResponse,
)

from services.Loan_application.reference_otp_service import (
    ReferenceOTPService,
)

router = APIRouter(
    prefix="/loan/application",
    tags=["Reference OTP"],
)


def get_client_ip(request: Request):
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP")
        or (request.client.host if request.client else "unknown")
    )


# ======================================================
# SEND OTP (AUTO USER DETECTION)
# ======================================================
@router.post("/references/send-otp")
def send_reference_otp(
    payload: ReferenceOTPSendRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    client_ip = get_client_ip(request)

    return ReferenceOTPService.send_reference_otp(
        db=db,
        user_id=current_user.id,
        mobile_number=payload.mobile_number,
        client_ip=client_ip,
    )


# ======================================================
# VERIFY OTP (AUTO USER + MOBILE)
# ======================================================
@router.post(
    "/references/verify-otp",
    response_model=ReferenceOTPVerifyResponse,
)
def verify_reference_otp(
    payload: ReferenceOTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    client_ip = get_client_ip(request)

    return ReferenceOTPService.verify_reference_otp(
        db=db,
        user_id=current_user.id,
        otp_code=payload.otp_code,
        client_ip=client_ip,
    )