from sqlalchemy.orm import Session
from uuid import UUID
from models.Loan_application.loan_application import LoanApplication

def create(db: Session, obj: LoanApplication):
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_by_id(db: Session, application_id: UUID):
    return (
        db.query(LoanApplication)
        .filter(LoanApplication.id == application_id)
        .first())

def update(db: Session, application: LoanApplication, data: dict):
    for field, value in data.items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application
