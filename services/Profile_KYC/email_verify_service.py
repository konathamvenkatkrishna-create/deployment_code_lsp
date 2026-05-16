import os
import random

from datetime import (
    datetime,
    timedelta
)

from fastapi import (
    HTTPException
)

from sqlalchemy.orm import (
    Session
)

from core.email_service import (
    sendmail
)

from models.Profile_KYC.user_profile import (
    UserProfile
)

from models.Auth.otp_verification import (
    OTPVerification
)


# =====================================================
# CONFIG
# =====================================================
OTP_EXPIRY_MINUTES = 5

OTP_RESEND_WAIT_SECONDS = 30

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "DEV"
)


# =====================================================
# SEND EMAIL OTP
# =====================================================
def send_email_verification_otp(

    db: Session,

    user_id: int
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    if not profile.email:

        raise HTTPException(
            status_code=400,
            detail="Email not found"
        )

    if profile.email_verified:

        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )

    # =============================================
    # CHECK RECENT OTP
    # =============================================
    recent_otp = db.query(
        OTPVerification
    ).filter(

        OTPVerification.user_id == user_id,

        OTPVerification.purpose == "EMAIL_VERIFY",

        OTPVerification.otp_status == "PENDING"

    ).order_by(
        OTPVerification.created_at.desc()
    ).first()

    if (

        recent_otp

        and datetime.utcnow()
        < (
            recent_otp.created_at
            + timedelta(
                seconds=OTP_RESEND_WAIT_SECONDS
            )
        )
    ):

        raise HTTPException(
            status_code=400,
            detail="Please wait before requesting OTP again"
        )

    # =============================================
    # GENERATE OTP
    # =============================================
    otp = str(
        random.randint(100000, 999999)
    )

    otp_record = OTPVerification(

        user_id=user_id,

        mobile_number="EMAIL",

        otp_hash=otp,

        expires_at=(
            datetime.utcnow()
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        ),

        otp_status="PENDING",

        purpose="EMAIL_VERIFY"
    )

    db.add(otp_record)

    db.commit()

    # =============================================
    # DEV MODE
    # =============================================
    if ENVIRONMENT.upper() == "DEV":

        print("\n")
        print("===================================")
        print("EMAIL OTP (DEV MODE)")
        print("===================================")
        print(f"Email : {profile.email}")
        print(f"OTP   : {otp}")
        print("===================================")
        print("\n")

        return {

            "success": True,

            "message": "OTP generated successfully",

            "dev_mode": True
        }

    # =============================================
    # PROD MODE
    # =============================================
    email_sent = sendmail(

        to=profile.email,

        subject="Email Verification OTP",

        body=(
            f"Your OTP is {otp}. "
            f"It is valid for "
            f"{OTP_EXPIRY_MINUTES} minutes."
        )
    )

    if not email_sent:

        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP"
        )

    return {

        "success": True,

        "message": "OTP sent successfully",

        "dev_mode": False
    }


# =====================================================
# VERIFY EMAIL OTP
# =====================================================
def verify_email_otp(

    db: Session,

    user_id: int,

    otp: str
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    otp_record = db.query(
        OTPVerification
    ).filter(

        OTPVerification.user_id == user_id,

        OTPVerification.purpose == "EMAIL_VERIFY",

        OTPVerification.otp_status == "PENDING"

    ).order_by(
        OTPVerification.created_at.desc()
    ).first()

    if not otp_record:

        raise HTTPException(
            status_code=404,
            detail="OTP not found"
        )

    # =============================================
    # OTP EXPIRED
    # =============================================
    if datetime.utcnow() > otp_record.expires_at:

        otp_record.otp_status = "EXPIRED"

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    # =============================================
    # INVALID OTP
    # =============================================
    if otp_record.otp_hash != otp:

        otp_record.attempts += 1

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    # =============================================
    # VERIFY EMAIL
    # =============================================
    profile.email_verified = True

    otp_record.otp_status = "VERIFIED"

    db.commit()

    db.refresh(profile)

    return {

        "success": True,

        "message": "Email verified successfully",

        "email": profile.email,

        "email_verified": profile.email_verified
    }