from datetime import datetime
from sqlalchemy.orm import Session

from repositories.Consent.consent_repository import ConsentRepository
from repositories.Consent.audit_repository import AuditRepository

def record_consent(db: Session, data):
    new_consent = ConsentRepository.create_user_consent(db, data)

    AuditRepository.log_action(
        db,
        action="CONSENT_ACCEPTED",
        user_id=data.user_id,
        details=f"{data.consent_type} v{data.version}"
    )

    return new_consent

def revoke_consent(db: Session, data):
    record = ConsentRepository.get_active_consent_record(
        db, data.user_id, data.consent_type
    )

    if record:
        ConsentRepository.revoke_consent(db, record)

    AuditRepository.log_action(
        db,
        action="CONSENT_REVOKED",
        user_id=data.user_id,
        details=data.consent_type
    )

    return {"message": "revoked"}


