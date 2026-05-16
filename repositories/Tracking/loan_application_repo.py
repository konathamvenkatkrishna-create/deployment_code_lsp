from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.Loan_application.loan_application import LoanApplication


class LoanApplicationRepository:
    @staticmethod
    def get_application(db: Session, application_id: int):
        return db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()
    
    @staticmethod
    def get_by_id(db: Session, application_id: int):
        return db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

    @staticmethod
    def get_user_applications(db: Session, user_id: int):
        return (
            db.query(LoanApplication)
            .filter(LoanApplication.user_profile_id == user_id)
            .order_by(desc(LoanApplication.id))
            .all()
        )

    @staticmethod
    def update_status(db: Session, application_id: int, new_status: str):
        app = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not app:
            return None

        app.application_status = (
        new_status.value
        if hasattr(new_status, "value")
        else new_status
        )
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def update_fields(db: Session, application_id: int, data: dict):
        app = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()

        if not app:
            return None

        for key, value in data.items():
            setattr(app, key, value)

        db.commit()
        db.refresh(app)
        return app