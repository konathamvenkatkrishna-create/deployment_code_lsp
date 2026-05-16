
from sqlalchemy.orm import Session
from models.Loan_application.loan_status_history import LoanStatusHistory


class LoanStatusHistoryRepository:

    @staticmethod
    def add(db: Session, app_id: int, old_status: str, new_status: str, comment: str = None):
        entry = LoanStatusHistory(
            application_id=app_id,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_timeline(db: Session, app_id: int):
        return (
            db.query(LoanStatusHistory)
            .filter(LoanStatusHistory.application_id == app_id)
            .order_by(LoanStatusHistory.created_at.asc())
            .all()
        )
    @staticmethod
    def insert_history(db: Session, application_id: int, old_status: str, new_status: str, source: str, comment: str = None):
        entry = LoanStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    
    @staticmethod
    def get_history(db: Session, application_id: int):
        return (
            db.query(LoanStatusHistory)
            .filter(LoanStatusHistory.application_id == application_id)
            .order_by(LoanStatusHistory.created_at.asc())
            .all()
        )