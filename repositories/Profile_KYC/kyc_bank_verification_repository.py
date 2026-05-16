from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from models.Profile_KYC.kyc_bank_verification import KYCBankVerification
 
class KYCBankVerificationRepository:

    @staticmethod
    def create_verification_log(
        db: Session,
        user_id: int,
        account_number: str,
        account_holder_name: str,
        bank_name: str,
        ifsc: str,
        name_match_percentage: float,
        status: str,
        failure_reason: Optional[str],
        attempt_number: int,
    ) -> KYCBankVerification:
        now = datetime.now(timezone.utc)
        log = KYCBankVerification(
            user_id               = user_id,
            account_number        = account_number,
            account_holder_name   = account_holder_name,
            bank_name             = bank_name,
            ifsc                  = ifsc,
            name_match_percentage = name_match_percentage,
            status                = status,
            failure_reason        = failure_reason,
            attempt_number        = attempt_number,
            created_at            = now,
            verified_at           = now if status == "VERIFIED" else None,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
 
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[KYCBankVerification]:

        return (
            db.query(KYCBankVerification)
            .filter(KYCBankVerification.user_id == user_id)
            .order_by(KYCBankVerification.created_at.desc())
            .all()
        )

    @staticmethod
    def get_latest_by_user_id(db: Session, user_id: int) -> Optional[KYCBankVerification]:
        return (
            db.query(KYCBankVerification)
            .filter(KYCBankVerification.user_id == user_id)
            .order_by(KYCBankVerification.created_at.desc())
            .first()
        )
 
    @staticmethod
    def get_verified_by_account_number(
        db: Session,
        account_number: str,
    ) -> Optional[KYCBankVerification]:
        return (
            db.query(KYCBankVerification)
            .filter(
                KYCBankVerification.account_number == account_number,
                KYCBankVerification.status         == "VERIFIED",
            )
            .first()
        )
 
    @staticmethod
    def delete_failed_verifications(db: Session, cutoff_date: datetime) -> int:
        count = (
            db.query(KYCBankVerification)
            .filter(
                KYCBankVerification.status.in_(["FAILED", "BLOCKED"]),
                KYCBankVerification.created_at < cutoff_date,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return count