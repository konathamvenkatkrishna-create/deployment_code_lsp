from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
import secrets
import requests

from models.Auth.otp_verification import OTPVerification
from models.Auth.email_verification import EmailVerification
from models.Auth.user import User
from models.Profile_KYC.user_profile import UserProfile
from core.security import hash_password, verify_password
from core.constants import (
    OTP_EXPIRY_SECONDS,
    MAX_VERIFY_ATTEMPTS,
    MAX_RESEND_ATTEMPTS,
    OTP_BLOCK_HOURS,
)

# =====================================================
# CONSTANTS
# =====================================================
PURPOSE_REGISTER = "REGISTER"
PURPOSE_EMAIL = "EMAIL"
PURPOSE_FORGOT_PASSWORD = "FORGOT_PASSWORD"
PURPOSE_2FA = "2FA"


DEV_MODE = True  # False in production

# =====================================================
# OTP GENERATOR
# =====================================================
def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)

# =====================================================
# MSG91 SEND OTP
# =====================================================
def send_msg91_otp(mobile: str, otp: str):
    if DEV_MODE:
        print("\n===== MSG91 OTP (DEV MODE) =====")
        print(f"Mobile : {mobile}")
        print(f"OTP    : {otp}")
        print("================================\n")
        return True

    raise HTTPException(500, "MSG91 disabled")

# =====================================================
# SEND OTP (REGISTER)
# =====================================================
def send_otp(
    db: Session,
    username: str | None,
    password: str | None,
    device_id: str,
    mobile_number: str,
    purpose: str,
):
    user = db.query(User).filter(User.mobile_number == mobile_number).first()

    # ✅ Create user only if not exists (REGISTER)
    if not user and purpose == PURPOSE_REGISTER:
        user = User(
            username=username,
            mobile_number=mobile_number,
            password_hash=hash_password(password),
            is_verified=False,
            is_active=False,
            device_id=device_id,
            Created_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()

    # ❗ DO NOT BLOCK VERIFIED USERS
    # Verified users may need OTP for:
    # - Login 2FA
    # - New device
    # - Password reset

    # Expire old OTPs of same purpose
    db.query(OTPVerification).filter(
        OTPVerification.mobile_number == mobile_number,
        OTPVerification.purpose == purpose,
        OTPVerification.otp_status == "PENDING",
    ).update({"otp_status": "EXPIRED"})

    otp = generate_otp()

    otp_row = OTPVerification(
        user_id=user.id if user else None,
        mobile_number=mobile_number,
        otp_hash=hash_password(otp),
        purpose=purpose,
        otp_status="PENDING",
        expires_at=datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS),
        attempts=0,
        resend_attempts=0,
        device_id=device_id,
        created_at=datetime.utcnow(),
    )

    db.add(otp_row)
    db.commit()

    send_msg91_otp(mobile_number, otp)

    return {"message": "OTP sent successfully"}

# =====================================================
# VERIFY OTP
# =====================================================
def verify_otp(
    db: Session,
    mobile_number: str,
    otp: str,
    device_id: str,
    purpose: str ,
):
    row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.mobile_number == mobile_number,
            OTPVerification.purpose == purpose,
            OTPVerification.otp_status == "PENDING",
        )
        .order_by(OTPVerification.id.desc())
        .first()
    )

    if not row:
        raise HTTPException(400, "OTP not found or expired")

    if row.device_id != device_id:
        raise HTTPException(403, "OTP requested from another device")

    if datetime.utcnow() > row.expires_at:
        row.otp_status = "EXPIRED"
        db.commit()
        raise HTTPException(400, "OTP expired")

    if row.attempts >= MAX_VERIFY_ATTEMPTS:
        row.otp_status = "BLOCKED"
        row.blocked_until = datetime.utcnow() + timedelta(hours=OTP_BLOCK_HOURS)
        db.commit()
        raise HTTPException(429, "Too many invalid attempts")

    row.attempts += 1

    if not verify_password(otp, row.otp_hash):
        db.commit()
        raise HTTPException(400, "Invalid OTP")

    row.otp_status = "VERIFIED"
    row.verified_at = datetime.utcnow()
    db.commit()
    
    return row

# =====================================================
# RESEND OTP
# =====================================================
def resend_otp(
    db: Session,
    mobile_number: str,
    device_id: str,
    purpose: str,
):
    row = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.mobile_number == mobile_number,
            OTPVerification.purpose == purpose,
            OTPVerification.otp_status.in_(["PENDING", "EXPIRED"]),
        )
        .order_by(OTPVerification.id.desc())
        .first()
    )
    if row.otp_status=="VERIFIED" :
        raise HTTPException(400,"otp already verified")
    if not row:
        raise HTTPException(400, "OTP session expired")

    if row.device_id != device_id:
        raise HTTPException(403, "OTP requested from another device")

    if row.resend_attempts >= MAX_RESEND_ATTEMPTS:
        row.otp_status = "BLOCKED"
        row.blocked_until = datetime.utcnow() + timedelta(hours=OTP_BLOCK_HOURS)
        db.commit()
        raise HTTPException(429, "Resend limit exceeded")

    otp = generate_otp()

    row.otp_hash = hash_password(otp)
    row.expires_at = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
    row.resend_attempts += 1
    row.otp_status = "PENDING"

    db.commit()
    send_msg91_otp(mobile_number, otp)

    return {
        "message": "OTP resent successfully",
        "remaining_resends": MAX_RESEND_ATTEMPTS - row.resend_attempts,
    }
#  send email otp (DEV MODE - PRINTS IN TERMINAL)
def sendemail_otp(email: str, otp: str):
    """
    DEV MODE
    Prints Email & OTP in terminal instead of sending
    """

    print("========== EMAIL OTP ==========")
    print(f"Email : {email}")
    print(f"OTP   : {otp}")
    print("================================")
    return  otp
    # Production (enable later)
    # payload = {
    #     "recipients": [
    #         {
    #             "to": email,
    #             "variables": {
    #                 "OTP": otp
    #             }
    #         }
    #     ],
    #     "from": {
    #         "email": "noreply@yourdomain.com"
    #     },
    #     "domain": "yourdomain.com",
    #     "template_id": "YOUR_MSG91_EMAIL_TEMPLATE_ID"
    # }
    #
    # headers = {
    #     "Content-Type": "application/json",
    #     "authkey": MSG91_AUTH_KEY
    # }
    #
    # response = requests.post(
    #     MSG91_EMAIL_OTP_URL,
    #     json=payload,
    #     headers=headers,
    #     timeout=5
    # )
    # response.raise_for_status()

# =====================================================
# SEND EMAIL OTP
# =====================================================
def send_email_otp(
    db: Session,
    email: str,
    device_id: str,
    purpose: str = PURPOSE_EMAIL,
):
    user = (
        db.query(User)
        .join(UserProfile)
        .filter(UserProfile.email == email)
        .first()
    )
    otp = generate_otp()

    otp_row = EmailVerification(
        user_id=user.id,
        email=email,
        device_id=device_id,
        otp_hash=hash_password(otp),
        purpose=purpose,
        otp_status="PENDING",
        expires_at=datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS),
        resend_attempts=0,
        attempts=0,
        created_at=datetime.utcnow(),
    )

    db.add(otp_row)
    db.commit()

    sendemail_otp(email, otp)
    return {"message": "Email OTP sent"}

# =====================================================
# VERIFY EMAIL OTP
# =====================================================
def verify_email_otp(
    db: Session,
    email: str,
    otp: str,
    device_id: str,
    purpose: str = PURPOSE_EMAIL ,
):
    row = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email,
            EmailVerification.device_id == device_id,
            EmailVerification.purpose == purpose,
            EmailVerification.otp_status == "PENDING",
        )
        .order_by(EmailVerification.id.desc())
        .first()
    )

    if not row:
        raise HTTPException(400, "OTP not found")
    if row.device_id != device_id:
        raise HTTPException(403, "OTP requested from another device")

    if datetime.utcnow() > row.expires_at:
        row.otp_status = "EXPIRED"
        db.commit()
        raise HTTPException(400, "OTP expired")

    row.attempts += 1

    if row.attempts > MAX_VERIFY_ATTEMPTS:
        row.otp_status = "BLOCKED"
        db.commit()
        raise HTTPException(429, "Too many attempts")

    if not verify_password(otp, row.otp_hash):
        db.commit()
        raise HTTPException(401, "Invalid OTP")

    row.otp_status = "VERIFIED"
    row.verified_at = datetime.utcnow()
    db.commit()

    return True
#resend email otp with limits
def resend_email_otp(
    db: Session,
    email: str,
    device_id: str | None = None,
    purpose: str = PURPOSE_EMAIL,
):
    otp_row = (
        db.query(EmailVerification)
        .filter(
            EmailVerification.email == email,
            EmailVerification.purpose == purpose,
            EmailVerification.otp_status.in_(["PENDING", "EXPIRED"]),
        )
        .order_by(EmailVerification.id.desc())
        .first()
    )

    if not otp_row:
        raise HTTPException(400, "OTP session expired. Generate a new OTP")

    if device_id is not None and otp_row.device_id != device_id:
        raise HTTPException(403, "OTP requested from another device")

    if otp_row.resend_attempts >= MAX_RESEND_ATTEMPTS:
        otp_row.otp_status = "BLOCKED"
        db.commit()
        raise HTTPException(429, "OTP resend limit exceeded")

    # ✅ regenerate OTP even if expired
    otp = generate_otp()

    otp_row.otp_hash = hash_password(otp)
    otp_row.expires_at = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
    otp_row.resend_attempts += 1
    otp_row.otp_status = "PENDING"

    db.commit()
    sendemail_otp(email, otp)

    return {
        "message": "Email OTP resent successfully",
        "remaining_resends": MAX_RESEND_ATTEMPTS - otp_row.resend_attempts,
    }