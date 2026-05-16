from sqlalchemy.orm import Session

from fastapi import HTTPException

import random

from datetime import (
    datetime,
    timedelta
)

from core.email_service import sendmail

from models.Auth.user import (
    User
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


# =====================================================
# UPDATE PROFILE
# =====================================================
def update_user_profile(

    db: Session,

    user: User,

    data: dict
):

    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    # =============================================
    # EMAIL UPDATE NOT ALLOWED HERE
    # =============================================
    if "email" in data:

        raise HTTPException(

            status_code=400,

            detail=(
                "Use OTP verification API "
                "to update email"
            )
        )

    # =============================================
    # UPDATE FIELDS
    # =============================================
    for key, value in data.items():

        if hasattr(profile, key):

            setattr(
                profile,
                key,
                value
            )

    db.commit()

    db.refresh(profile)

    return profile


# =====================================================
# DELETE USER ACCOUNT
# =====================================================
def delete_user_account(

    db: Session,

    user: User
):

    user.is_active = False

    db.commit()

    db.refresh(user)

    return {

        "message":
            "Account deleted successfully"
    }


# =====================================================
# SEND OTP TO REGISTERED EMAIL
# =====================================================
def send_otp_to_old_email(

    db: Session,

    user: User
):

    # =============================================
    # FETCH PROFILE
    # =============================================
    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    if not profile.email:

        raise HTTPException(

            status_code=400,

            detail="Email not found"
        )

    # =============================================
    # CHECK RESEND LIMIT
    # =============================================
    recent_otp = db.query(
        OTPVerification
    ).filter(

        OTPVerification.user_id
        == user.id,

        OTPVerification.purpose
        == "EMAIL_VERIFY",

        OTPVerification.otp_status
        == "PENDING"

    ).order_by(
        OTPVerification.created_at.desc()
    ).first()

    if (

        recent_otp

        and datetime.utcnow()
        < (
            recent_otp.created_at
            + timedelta(
                seconds=
                OTP_RESEND_WAIT_SECONDS
            )
        )
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Please wait before "
                "requesting OTP again"
            )
        )

    # =============================================
    # GENERATE OTP
    # =============================================
    otp = str(
        random.randint(100000, 999999)
    )

    # =============================================
    # SAVE OTP
    # =============================================
    otp_record = OTPVerification(

        user_id=
            user.id,

        mobile_number=
            "EMAIL",

        otp_hash=
            otp,

        expires_at=
            datetime.utcnow()
            + timedelta(
                minutes=
                OTP_EXPIRY_MINUTES
            ),

        otp_status=
            "PENDING",

        purpose=
            "EMAIL_VERIFY"
    )

    db.add(otp_record)

    db.commit()

    # =============================================
    # SEND EMAIL
    # =============================================
    email_sent = sendmail(

        to=
            profile.email,

        subject=
            "Email Verification OTP",

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

        "success":
            True,

        "message":
            "OTP sent successfully"
    }


# =====================================================
# VERIFY OTP & UPDATE EMAIL
# =====================================================
def verify_otp_and_update_email(

    db: Session,

    user: User,

    new_email: str,

    otp: str
):

    # =============================================
    # FETCH PROFILE
    # =============================================
    profile = db.query(
        UserProfile
    ).filter(
        UserProfile.user_id
        == user.id
    ).first()

    if not profile:

        raise HTTPException(

            status_code=404,

            detail="Profile not found"
        )

    # =============================================
    # FETCH OTP
    # =============================================
    otp_record = db.query(
        OTPVerification
    ).filter(

        OTPVerification.user_id
        == user.id,

        OTPVerification.purpose
        == "EMAIL_VERIFY",

        OTPVerification.otp_status
        == "PENDING"

    ).order_by(
        OTPVerification.created_at.desc()
    ).first()

    if not otp_record:

        raise HTTPException(

            status_code=400,

            detail="OTP not generated"
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

        raise HTTPException(

            status_code=400,

            detail="Invalid OTP"
        )

    # =============================================
    # SAME EMAIL
    # =============================================
    if profile.email == new_email:

        raise HTTPException(

            status_code=400,

            detail=(
                "New email must "
                "be different"
            )
        )

    # =============================================
    # EMAIL EXISTS
    # =============================================
    existing_email = db.query(
        UserProfile
    ).filter(
        UserProfile.email
        == new_email
    ).first()

    if existing_email:

        raise HTTPException(

            status_code=400,

            detail="Email already exists"
        )

    # =============================================
    # UPDATE EMAIL
    # =============================================
    profile.email = new_email

    profile.email_verified = True

    otp_record.otp_status = "VERIFIED"

    db.commit()

    db.refresh(profile)

    return {

        "success":
            True,

        "message":
            "Email updated successfully",

        "email":
            profile.email
    }