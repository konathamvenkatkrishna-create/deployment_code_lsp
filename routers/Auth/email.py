from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user
from core.security import verify_password, create_access_token, create_refresh_token

from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from models.Auth.user_device import UserDevice

from services.Auth.otp_services import (
    send_email_otp,
    verify_email_otp,
    resend_email_otp,
    PURPOSE_EMAIL,
)

from schemas.Auth.email import (
    LoginEmail2FASchema,
    VerifyEmail2FASchema,
    DisableEmail2FASchema,
    SendEmail2FASchema,   # ✅ FIXED IMPORT
)

router = APIRouter(tags=["Email 2FA"])


# =====================================================
# ENABLE EMAIL 2FA
# =====================================================
@router.post("/2fa/email/enable")
def enable_email_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.two_factor_enabled:
        raise HTTPException(400, "Email 2FA already enabled")

    current_user.two_factor_enabled = True
    db.commit()

    return {"message": "Email 2FA enabled successfully"}


# =====================================================
# LOGIN (PASSWORD + DEVICE CHECK)
# =====================================================
@router.post("/2fa/email/login")
def login_email_2fa(
    data: LoginEmail2FASchema,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.mobile_number == data.mobile,
            User.is_verified == True,
            User.is_active == True,
        )
        .first()
    )

    if not user:
        raise HTTPException(401, "User not found or not verified")
    if not user.two_factor_enabled:
        raise HTTPException(401,"user not enabled two factor verification")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # 🔍 Check device
    device = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.device_id == data.device_id,
    ).first()

    # 🔐 OTP REQUIRED CONDITIONS
    otp_required = user.two_factor_enabled or not device

    if otp_required:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user.id)
            .first()
        )

        if not profile or not profile.email:
            raise HTTPException(400, "Email not registered")

        # send_email_otp_db(
        #     db=db,
        #     email=profile.email,
        #     device_id=data.device_id,
        # )

        return {
            "otp_required": True,
            "next": "send otp to email"
        }

    # ✅ Same device + 2FA disabled → direct login
    device.last_login_at = datetime.utcnow()
    db.commit()
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role   # 🔥 IMPORTANT FIX
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "otp_required": False,
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
#send_email_otp_db
@router.post("/otp/email/send")
def send_emailotp(
    data: SendEmail2FASchema,
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.email == data.email).first()

    if not profile:
        raise HTTPException(404, "Profile not found ")

    send_email_otp(
        db=db,
        email=profile.email,
        device_id=data.device_id,
    )

    return {"message": "OTP sent to registered email"}

# =====================================================
# VERIFY EMAIL OTP
# =====================================================
@router.post("/2fa/email/verify")
def verify_emailotp(
    data: VerifyEmail2FASchema,
    db: Session = Depends(get_db),
):
    # ✅ Verify OTP
    verify_email_otp(
        db=db,
        email=data.email,
        otp=data.otp,
        device_id=data.device_id,
    )

    user = (
        db.query(User)
        .join(UserProfile)
        .filter(UserProfile.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(404, "User not found")

    # 🔐 Bind / update device
    device = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.device_id == data.device_id,
    ).first()

    if not device:
        db.add(
            UserDevice(
                user_id=user.id,
                device_id=data.device_id,
                last_login_at=datetime.utcnow(),
            )
        )
    else:
        device.last_login_at = datetime.utcnow()

    db.commit()
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role   # 🔥 IMPORTANT FIX
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "message": "Login successful",
        "access_token":access_token,
        "refresh_token": refresh_token,
    }


# =====================================================
# DISABLE EMAIL 2FA
# =====================================================
@router.post("/2fa/email/disable")
def disable_email_2fa(
    data: DisableEmail2FASchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.two_factor_enabled:
        raise HTTPException(400, "Email 2FA already disabled")

    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(401, "Invalid password")

    current_user.two_factor_enabled = False
    db.commit()

    return {"message": "Email 2FA disabled successfully"}

@router.post("/otp/email/resend")
def resend_email_otp(
    data: SendEmail2FASchema,
    db: Session = Depends(get_db),
):
    result = resend_email_otp(
        db=db,
        email=data.email,
        device_id=data.device_id,
    )

    return result