from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random
import hashlib
from fastapi import HTTPException

from core.sms import send_sms_msg91
from core.config import settings

from models.Loan_application.loan_application import LoanApplication
from models.Loan_application.loan_application_steps import LoanApplicationStepTracker
from models.Loan_application.loan_application_references import LoanApplicationReference

from repositories.Loan_application.loan_application_reference_repo import (
    LoanApplicationReferenceRepository
)

from core.enums import LoanApplicationStep, enum_value


COOLDOWN_SECONDS = 30
OTP_EXPIRY_SECONDS = 300
MAX_ATTEMPTS = 3


class ReferenceOTPService:

    # =====================================================
    # SEND OTP (DB BASED)
    # =====================================================
    @staticmethod
    def send_reference_otp(db: Session, user_id: int, mobile_number: str, client_ip: str):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No active draft application found")

        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application.id
        )

        reference = next((r for r in references if r.mobile_number == mobile_number), None)

        if not reference:
            raise HTTPException(404, "Reference not found")

        now = datetime.utcnow()

        # 🔥 COOLDOWN CHECK
        if reference.otp_last_sent_at and (
            now - reference.otp_last_sent_at
        ).total_seconds() < COOLDOWN_SECONDS:
            raise HTTPException(400, "Wait before requesting OTP")

        # 🔥 GENERATE OTP
        otp_plain = str(random.randint(100000, 999999))
        hashed_otp = hashlib.sha256(otp_plain.encode()).hexdigest()

        # 🔥 STORE IN DB
        reference.otp_hash = hashed_otp
        reference.otp_attempts = 0
        reference.otp_expires_at = now + timedelta(seconds=OTP_EXPIRY_SECONDS)
        reference.otp_last_sent_at = now

        db.commit()

        # DEV MODE
        if settings.ENV.lower() == "dev":
            print(f"\n📲 Reference OTP for {mobile_number}: {otp_plain}\n")

        # PROD MODE
        else:
            try:
                send_sms_msg91(mobile_number, otp_plain)
            except Exception as e:
                raise HTTPException(500, f"Failed to send OTP: {str(e)}")

        return {"message": "OTP sent successfully"}

    # =====================================================
    # VERIFY OTP
    # =====================================================
    @staticmethod
    def verify_reference_otp(
        db: Session,
        user_id: int,
        otp_code: str,
        client_ip: str = None
    ):

        application = db.query(LoanApplication).filter(
            LoanApplication.user_profile_id == user_id,
            LoanApplication.is_submitted == False
        ).order_by(LoanApplication.id.desc()).first()

        if not application:
            raise HTTPException(404, "No active draft application found")

        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application.id
        )

        reference = next(
            (r for r in references if not r.is_verified),
            None
        )

        if not reference:
            raise HTTPException(400, "No pending reference verification")

        now = datetime.utcnow()

        # 🔥 EXPIRED
        if not reference.otp_expires_at or reference.otp_expires_at < now:
            raise HTTPException(400, "OTP expired")

        # 🔥 MAX ATTEMPTS
        if reference.otp_attempts >= MAX_ATTEMPTS:
            raise HTTPException(400, "Too many attempts")

        hashed_input = hashlib.sha256(otp_code.encode()).hexdigest()

        if hashed_input != reference.otp_hash:
            reference.otp_attempts += 1
            db.commit()
            raise HTTPException(400, "Invalid OTP")

        # ✅ SUCCESS
        reference.is_verified = True
        reference.otp_hash = None
        reference.otp_attempts = 0

        db.commit()
        db.refresh(reference)

        if client_ip:
            print(f"✅ OTP verified for reference {reference.id} from IP {client_ip}")

        ReferenceOTPService.update_application_step_if_references_verified(
            db, reference.application_id
        )

        return {
            "reference_id": reference.id,
            "verified": True,
            "verified_at": datetime.now(timezone.utc)
        }

    # =====================================================
    # STEP UPDATE
    # =====================================================
    @staticmethod
    def update_application_step_if_references_verified(db: Session, application_id: int):

        references = LoanApplicationReferenceRepository.get_by_application_id(
            db, application_id
        )

        if not references:
            return

        if all(ref.is_verified for ref in references):

            tracker = db.query(LoanApplicationStepTracker).filter_by(
                application_id=application_id
            ).first()

            if not tracker:
                return

            tracker.references_completed = True
            tracker.last_completed_step = enum_value(
                LoanApplicationStep.REFERENCES
            )
            tracker.current_step = enum_value(
                LoanApplicationStep.DECLARATION
            )

            application = db.get(LoanApplication, application_id)

            if application:
                application.current_step = enum_value(
                    LoanApplicationStep.DECLARATION
                )

            db.commit()