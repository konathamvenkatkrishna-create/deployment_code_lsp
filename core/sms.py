import requests
import secrets
from datetime import datetime
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from core.config import settings
from core.security import hash_password
from models.Auth.otp_verification import OTPVerification


# =====================================================
# 📱 SEND SMS (MSG91)
# =====================================================
def send_sms_msg91(mobile: str, otp: str):
    """
    Send OTP via MSG91 Flow API
    """

    # =========================
    # DEV MODE
    # =========================
    if not settings.SMS_ENABLED:
        print("========== SMS (DEV MODE) ==========")
        print(f"Mobile : {mobile}")
        print(f"OTP    : {otp}")
        print("===================================")
        return {"status": "dev"}

    # =========================
    # VALIDATION
    # =========================
    if not settings.MSG91_API_KEY:
        raise HTTPException(500, "MSG91_API_KEY missing")

    if not settings.MSG91_FLOW_ID:
        raise HTTPException(500, "MSG91_FLOW_ID missing")

    if not settings.MSG91_SENDER_ID:
        raise HTTPException(500, "MSG91_SENDER_ID missing")

    url = "https://api.msg91.com/api/v5/flow/"

    payload = {
        "flow_id": settings.MSG91_FLOW_ID,
        "sender": settings.MSG91_SENDER_ID,
        "mobiles": f"{settings.COUNTRY_CODE}{mobile}",
        "OTP": otp
    }

    headers = {
        "authkey": settings.MSG91_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            raise HTTPException(500, f"MSG91 Error: {response.text}")

        return {"status": "success"}

    except requests.exceptions.Timeout:
        raise HTTPException(500, "SMS timeout")

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, f"SMS failed: {str(e)}")


# =====================================================
# 🔐 GENERATE OTP (SECURE)
# =====================================================
def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


# =====================================================
# 📦 GET ACTIVE OTP RECORD
# =====================================================
def get_active_record(db: Session, mobile_number: str) -> OTPVerification | None:
    record = (
        db.query(OTPVerification)
        .filter(OTPVerification.mobile_number == mobile_number)
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if not record:
        return None

    # ⏰ Expiry check
    if record.expires_at and datetime.utcnow() > record.expires_at:
        return None

    return record


# =====================================================
# 🚫 CHECK BLOCK STATUS
# =====================================================
def is_blocked(record: OTPVerification) -> bool:
    if record and record.blocked_until:
        return datetime.utcnow() < record.blocked_until
    return False


# =====================================================
# 🔐 HASH OTP
# =====================================================
def hash_otp(otp: str) -> str:
    return hash_password(otp)


# =====================================================
# 📱 GET DEVICE ID
# =====================================================
def get_device_id(request: Request) -> str:
    device_id = request.headers.get("X-Device-ID")

    if not device_id or len(device_id.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Valid Device ID (X-Device-ID) is required"
        )

    return device_id.strip()