from sqlalchemy.orm import Session
from datetime import datetime
from models.Consent.consent_master import ConsentMaster
from models.Consent.user_consent import UserConsent

class ConsentRepository:

    @staticmethod
    def get_latest_by_type(db: Session, type: str):
        return (
            db.query(ConsentMaster)
            .filter(ConsentMaster.type == type)
            .order_by(ConsentMaster.id.desc())
            .first()
        )

    @staticmethod
    def create_user_consent(db: Session, data):
        consent = UserConsent(
            user_id=data.user_id,
            consent_type=data.consent_type,
            version=data.version,
            accepted=data.accepted,
            scroll_completed=data.scroll_completed,
            device_info=data.device_info,
            ip_address=data.ip_address,
            accepted_at=datetime.utcnow(),
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def get_active_consent_record(db: Session, user_id: int, consent_type: str):
        return (
            db.query(UserConsent)
            .filter(
                UserConsent.user_id == user_id,
                UserConsent.consent_type == consent_type,
                UserConsent.revoked_at.is_(None)
            )
            .first()
        )

    @staticmethod
    def revoke_consent(db: Session, record):
        record.revoked_at = datetime.utcnow()
        db.commit()
        return record

