from sqlalchemy.orm import Session
from models.Profile_KYC.kyc_pan_verification import KYCPANVerification
from typing import List, Optional
from datetime import datetime, timezone

class KYCPANVerificationRepository:

    @staticmethod
    def create_verification_log(
        db: Session,
        user_id: int,
        pan_number: str,
        full_name_submitted: str,
        verified_name: str,
        match_percentage: float,
        name_match: bool,
        status: str,
        failure_reason: Optional[str],
        attempt_number: int,
    ) -> KYCPANVerification:
        log = KYCPANVerification(
            user_id             = user_id,
            pan_number          = pan_number,
            full_name_submitted = full_name_submitted,
            verified_name       = verified_name,
            match_percentage    = match_percentage,
            name_match          = name_match,
            status              = status,
            failure_reason      = failure_reason,
            attempt_number      = attempt_number,
            created_at          = datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[KYCPANVerification]:
        return db.query(KYCPANVerification).filter(
            KYCPANVerification.user_id == user_id
        ).order_by(KYCPANVerification.created_at.desc()).all()

    @staticmethod
    def get_latest_by_user_id(db: Session, user_id: int) -> Optional[KYCPANVerification]:
        return db.query(KYCPANVerification).filter(
            KYCPANVerification.user_id == user_id
        ).order_by(KYCPANVerification.created_at.desc()).first()

    @staticmethod
    def delete_failed_verifications(db: Session, cutoff_date: datetime) -> int:
        count = db.query(KYCPANVerification).filter(
            KYCPANVerification.status.in_(["FAILED", "BLOCKED"]),
            KYCPANVerification.created_at < cutoff_date,
        ).delete(synchronize_session=False)
        db.commit()
        return count
