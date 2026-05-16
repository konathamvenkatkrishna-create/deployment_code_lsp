from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_biometric_signature,
)
from core.validators import validate_mobile_number
from core.dependencies import get_current_user
from models.Auth.user import User
from models.Auth.user_device import UserDevice
from services.Auth.otp_services import send_otp, verify_otp

from schemas.Auth.biometric import (
    BiometricLoginSchema,
    VerifyBiometricOTPSchema,
    EnableBiometricSchema,
    DisableBiometricSchema,
)

router = APIRouter(tags=["Biometric"])


# =====================================================
# ENABLE BIOMETRIC (TRUSTED DEVICE ONLY)
# =====================================================
@router.post("/enable-biometric")
def enable_biometric(
    data: EnableBiometricSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == current_user.id,
            UserDevice.device_id == data.device_id,
        )
        .first()
    )

    if not device:
        raise HTTPException(403, "Untrusted device")

    current_user.biometric_enabled = True
    current_user.biometric_type = data.biometric_type
    current_user.biometric_key = data.biometric_key
    db.commit()

    return {"message": "Biometric enabled successfully"}


# =====================================================
# DISABLE BIOMETRIC (TRUSTED DEVICE ONLY)
# =====================================================
@router.post("/disable-biometric")
def disable_biometric(
    data: DisableBiometricSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == current_user.id,
            UserDevice.device_id == data.device_id,
        )
        .first()
    )

    if not device:
        raise HTTPException(403, "Untrusted device")

    current_user.biometric_enabled = False
    current_user.biometric_key = None
    current_user.biometric_type = None
    db.commit()

    return {"message": "Biometric disabled successfully"}


# =====================================================
# BIOMETRIC LOGIN
# =====================================================
@router.post("/biometric-login")
def biometric_login(
    data: BiometricLoginSchema,
    db: Session = Depends(get_db),
):
    mobile = validate_mobile_number(data.mobile_number)

    user = db.query(User).filter(User.is_verified == True,
        User.mobile_number == mobile
    ).first()

    if not user:
        raise HTTPException(401, "User not found or not verified") 
    if not user.biometric_enabled:
        raise HTTPException(401, "Biometric not enabled")

    if user.biometric_type != data.biometric_type:
        raise HTTPException(401, "Biometric type mismatch")

    device = db.query(UserDevice).filter(
        UserDevice.user_id == user.id,
        UserDevice.device_id == data.device_id,
    ).first()

    # ✅ TRUSTED DEVICE → VERIFY BIOMETRIC
    if device:
        if not verify_biometric_signature(
            data.biometric_signature,
            user.biometric_key,
        ):
            raise HTTPException(401, "Biometric verification failed")

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
            "otp_required": False,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # 🔐 NEW DEVICE → SEND OTP
    send_otp(
        db=db,
        mobile_number=mobile,
        username=user.username,      # ✅ RECOMMENDED
        device_id=data.device_id,
    )

    return {
        "otp_required": True,
        "message": "New device detected. OTP sent to registered mobile.",
    }
# =====================================================
# VERIFY OTP FOR NEW DEVICE
# =====================================================
@router.post("/verify-biometric-otp")
def verify_biometric_otp(
    data: VerifyBiometricOTPSchema,
    db: Session = Depends(get_db),
):
    mobile = validate_mobile_number(data.mobile_number)

    # ✅ VERIFY OTP (DEVICE-BOUND)
    verify_otp(
        db=db,
        mobile_number=mobile,
        otp=data.otp,
        device_id=data.device_id,
    )

    user = (
        db.query(User)
        .filter(User.mobile_number == mobile)
        .first()
    )

    if not user:
        raise HTTPException(404, "User not found")


    existing_device = (
        db.query(UserDevice)
        .filter(
            UserDevice.user_id == user.id,
            UserDevice.device_id == data.device_id,
        )
        .first()
    )

    if not existing_device:
        db.add(
            UserDevice(
                user_id=user.id,
                device_id=data.device_id,
                created_at=datetime.utcnow(),
            )
        )
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
        "message": "Biometric login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }