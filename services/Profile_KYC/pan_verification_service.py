from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.Profile_KYC.attempt_tracker import VerificationType
from repositories.Profile_KYC.user_repository import UserRepository
from repositories.Profile_KYC.attempt_tracker_repository import AttemptTrackerRepository
from repositories.Profile_KYC.kyc_pan_verification_repository import KYCPANVerificationRepository
from repositories.Profile_KYC.dummy_pan_repository import DummyPANRepository
from utils.name_matcher import name_match_percentage
from core.config import settings


class PANVerificationService:

    @staticmethod
    def verify_pan(db: Session, user_id: int) -> dict:
        user = UserRepository.get_by_user_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")
        if user.pan_status == "VERIFIED":
            return {
                "message":         "PAN already verified",
                "pan_status":      "VERIFIED",
                "next_step":       "Proceed to Aadhaar verification",
            }

        tracker = AttemptTrackerRepository.get_by_email_and_type(db, user.email, VerificationType.PAN)
        if not tracker:
            tracker = AttemptTrackerRepository.create_tracker(db, user.email, VerificationType.PAN)
        
        now = datetime.now(timezone.utc)

        if tracker.locked_until and tracker.locked_until > now:
            raise HTTPException(
                423,
                f"Verification blocked due to {settings.PAN_MAX_ATTEMPTS} failed attempts. "
                f"Try after {settings.PAN_COOLDOWN_HOURS} hours."
            )

        if tracker.locked_until and tracker.locked_until <= now:
            AttemptTrackerRepository.reset_attempts(db, tracker)

        current_attempt = AttemptTrackerRepository.increment_attempt(db, tracker)
        

        if current_attempt > settings.PAN_MAX_ATTEMPTS:
            AttemptTrackerRepository.lock_tracker(db, tracker, now + timedelta(hours=settings.PAN_COOLDOWN_HOURS))
            
            raise HTTPException(
                423,
                f"Maximum attempts ({settings.PAN_MAX_ATTEMPTS}) exceeded. "
                f"Account blocked for {settings.PAN_COOLDOWN_HOURS} hours."
            )

        pan_record = DummyPANRepository.get_by_pan_number(db, user.pan_number)
        
        failure_reason = None
        verified_name = ""
        match_pct = 0.0

        if not pan_record:
            failure_reason = "PAN not found in records"
        else:
            verified_name = pan_record.full_name
            match_pct = name_match_percentage(user.full_name, pan_record.full_name)
            if match_pct < settings.NAME_MATCH_THRESHOLD:
                failure_reason = "Name does not match PAN records"
        
        if failure_reason:
            if current_attempt >= settings.PAN_MAX_ATTEMPTS:
                status = "BLOCKED"
                AttemptTrackerRepository.lock_tracker(db, tracker, now + timedelta(hours=settings.PAN_COOLDOWN_HOURS))
                user.pan_status = "BLOCKED"
                message_suffix = f"Maximum attempts reached. Account blocked for {settings.PAN_COOLDOWN_HOURS} hours."
            else:
                status = "FAILED"
                user.pan_status = "FAILED"
                remaining = settings.PAN_MAX_ATTEMPTS - current_attempt
                message_suffix = f"{remaining} attempt(s) remaining."
            
            KYCPANVerificationRepository.create_verification_log(
                db=db,
                user_id=user.user_id,
                pan_number=user.pan_number,
                full_name_submitted=user.full_name,
                verified_name=verified_name if verified_name else "",
                match_percentage=match_pct,
                name_match=False,
                status=status,
                failure_reason=failure_reason,
                attempt_number=current_attempt
            )
            
            UserRepository.update_user(db, user)
            
            if status == "BLOCKED":
                raise HTTPException(423, f"{failure_reason}. {message_suffix}")
            else:
                raise HTTPException(400, f"{failure_reason}. {message_suffix}")
        
        user.pan_status = "VERIFIED"
        user.verified_name = verified_name
        user.pan_locked = True
        user.name_locked = True
        user.pan_verified_at = now
        
        KYCPANVerificationRepository.create_verification_log(
            db=db,
            user_id=user.user_id,
            pan_number=user.pan_number,
            full_name_submitted=user.full_name,
            verified_name=verified_name,
            match_percentage=match_pct,
            name_match=True,
            status="VERIFIED",
            failure_reason=None,
            attempt_number=current_attempt
        )
        
        AttemptTrackerRepository.reset_attempts(db, tracker)
        UserRepository.update_user(db, user)
        
        return {
            "message": "PAN verified successfully",
            "pan_status": "VERIFIED",
            "next_step": "Proceed to Aadhaar verification"
        }
            