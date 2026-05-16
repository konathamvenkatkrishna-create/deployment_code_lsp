from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from core.security import hash_password
from core.validators import validate_mobile_number
from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from models.Auth.otp_verification import OTPVerification
from models.Auth.email_verification import EmailVerification
from services.Auth.otp_services import (
    send_otp,
    resend_otp,
    verify_otp,
    send_email_otp,
    resend_email_otp,
    verify_email_otp,
    PURPOSE_FORGOT_PASSWORD,
)

from schemas.Auth.forgot_password import (
    ForgotPasswordmobile,
    ForgotPasswordEmail,
    VerifyOtpmobile,
    VerifyOtpEmail,
    ResetPasswordMobileRequest,
    ResetPasswordEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["Forgot Password"])
@router.post("/otp/mobile/send")
def send_mobile_otp(data: ForgotPasswordmobile, db: Session = Depends(get_db)):
    mobile = validate_mobile_number(data.mobile)

    user = db.query(User).filter(User.mobile_number == mobile).first()
    if not user:
        raise HTTPException(404, "User not found")

    send_otp(
        db=db,
        mobile_number=data.mobile,
        username=user.username,
        password=user.password_hash,
        device_id=None,   # forgot password → no device binding
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "OTP sent to mobile"}
@router.post("/otp/mobile/verify")
def verify_mobile_otp(data: VerifyOtpmobile, db: Session = Depends(get_db)):
    mobile = validate_mobile_number(data.mobile)

    verify_otp(
        db=db,
        mobile_number=mobile,
        otp=data.otp,
        device_id=None,
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "Mobile OTP verified"}
@router.post("/reset-password/mobile")
def reset_password_mobile(
    data: ResetPasswordMobileRequest,
    db: Session = Depends(get_db),
):
    mobile = validate_mobile_number(data.mobile)

    otp_row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.mobile_number == mobile,
            OTPVerification.otp_status == "VERIFIED",OTPVerification.purpose == PURPOSE_FORGOT_PASSWORD
        )
        .order_by(OTPVerification.id.desc())
        .first()
    )

    if not otp_row:
        raise HTTPException(403, "OTP verification required")

    user = db.query(User).filter(
        User.mobile_number == mobile
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.password_hash = hash_password(data.new_password)

    db.delete(otp_row)  # single-use OTP
    db.commit()

    return {"message": "Password reset successful"}
@router.post("/otp/mobile/resend")
def resend_mobile_otp(data: ForgotPasswordmobile, db: Session = Depends(get_db)):
    mobile = validate_mobile_number(data.mobile)

    resend_otp(
        db=db,
        mobile_number=mobile,
        device_id=None,
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "OTP resent to mobile"}
@router.post("/otp/email/send")
def send_email_otp_api(data: ForgotPasswordEmail, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(
        UserProfile.email == data.email
    ).first()

    if not profile:
        raise HTTPException(404, "User not found")

    send_email_otp(
        db=db,
        email=data.email,
        device_id=None,
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "OTP sent to email"}
@router.post("/otp/email/verify")
def verify_email_otp(data: VerifyOtpEmail, db: Session = Depends(get_db)):
    verify_email_otp(
        db=db,
        email=data.email,
        otp=data.email_otp,
        device_id=None,
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "Email OTP verified"}
@router.post("/otp/email/resend")
def resend_email_otp(data: ForgotPasswordEmail, db: Session = Depends(get_db)):
    resend_email_otp(
        db=db,
        email=data.email,
        device_id=None,
        purpose=PURPOSE_FORGOT_PASSWORD,
    )

    return {"message": "OTP resent to email"}

@router.post("/reset-password/email")
def reset_password_email(
    data: ResetPasswordEmailRequest,
    db: Session = Depends(get_db),
):
    otp_row = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == data.email,
            EmailVerification.otp_status == "VERIFIED",
            EmailVerification.purpose == PURPOSE_FORGOT_PASSWORD
        )
        .order_by(EmailVerification.id.desc())
        .first()
    )

    if not otp_row:
        raise HTTPException(403, "OTP verification required")

    profile = db.query(UserProfile).filter(
        UserProfile.email == data.email
    ).first()

    if not profile:
        raise HTTPException(404, "User not found")

    user = db.query(User).filter(
        User.id == profile.user_id
    ).first()

    user.password_hash = hash_password(data.new_password)

    db.delete(otp_row)
    db.commit()

    return {"message": "Password reset successful"}