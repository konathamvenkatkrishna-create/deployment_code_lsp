from sqlalchemy.orm import Session
from app.models.audit_logs import AuditLog

class AuditRepository:

    @staticmethod
    def log_action(db: Session, action: str, user_id: int, details: str | None = None):
        entry = AuditLog(
            action=action,
            user_id=user_id,
            details=details
        )
        db.add(entry)
        db.commit()
        return entry

    @staticmethod
    def get_all_logs(db: Session):
        return db.query(AuditLog).order_by(AuditLog.id.desc()).all()
