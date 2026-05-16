from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from models.Auth.user import User
from models.Auth.user_device import UserDevice
from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from services.Auth.otp_services import send_otp, verify_otp,PURPOSE_2FA
from core.dependencies import get_current_user
from schemas.Auth.twofactor import (
    Login2FASchema,
    Verify2FASchema,
    Disable2FASchema,
    Send2FASchema,   # ✅ FIXED
)

router = APIRouter(tags=["2FA"])


# ==============================
# ENABLE MOBILE OTP 2FA
# ==============================
@router.post("/2fa/mobile/enable")
def enable_mobile_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.two_factor_enabled:
        raise HTTPException(400, "Mobile 2FA already enabled")

    current_user.two_factor_enabled = True
    db.commit()

    return {"message": "Mobile OTP 2FA enabled successfully"}


# ==============================
# LOGIN
# ==============================
@router.post("/2fa/mobile/login")
def login(
    data: Login2FASchema,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.mobile_number == data.mobile,
        User.is_verified == True,
        User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(401, "User not found or not verified")
    if not user.two_factor_enabled:
       raise HTTPException(401,"user not enabled two factor verification")

    # 1️⃣ Validate password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # 2️⃣ Check device
    device = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.device_id == data.device_id,
    ).first()

    otp_required = False

    # 3️⃣ OTP decision
    if user.two_factor_enabled:
        otp_required = True
    elif not device:
        otp_required = True  # device mismatch

    if otp_required:
        send_otp(
            db=db,
            mobile_number=user.mobile_number,
            username=user.username,
            password=user.password_hash,
            device_id=data.device_id,
            purpose=PURPOSE_2FA,
        )

        return {
            "otp_required": True,
            "message": "OTP sent to registered mobile",
        }

    # 4️⃣ Login success (same device + no 2FA)
    device.last_login_at = datetime.utcnow()
    db.commit()

    return {
        "otp_required": False,
        "message": "Login successful",
       "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token(user.id),
    }

# ==============================
# VERIFY MOBILE OTP
# ==============================
@router.post("/2fa/mobile/verify")
def verify_mobile_otp(
    data: Verify2FASchema,
    db: Session = Depends(get_db),
):
    otp_row = verify_otp(
        db=db,
        mobile_number=data.mobile,
        otp=data.otp,
        device_id=data.device_id,
        purpose=PURPOSE_2FA,
    )

    user = db.query(User).filter(User.mobile_number == otp_row.mobile_number).first()
    if not user:
        raise HTTPException(404, "User not found")

    # 🔒 Bind device after OTP
    device = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.device_id == data.device_id,
    ).first()

    if not device:
        db.add(
            UserDevice(
                user_id=user.id,
                device_id=data.device_id,
                created_at=datetime.utcnow(),
            )
        )
    else:
        device.last_login_at = datetime.utcnow()

    db.delete(otp_row)
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
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
# ==============================
# DISABLE MOBILE OTP 2FA
# ==============================
@router.post("/2fa/mobile/disable")
def disable_mobile_2fa(
    data: Disable2FASchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.two_factor_enabled:
        raise HTTPException(400, "Mobile 2FA already disabled")

    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(401, "Invalid password")

    current_user.two_factor_enabled = False
    db.commit()

    return {"message": "Mobile OTP 2FA disabled successfully"}