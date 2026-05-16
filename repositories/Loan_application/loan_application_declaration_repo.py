from sqlalchemy.orm import Session
from app.db_models.loan_application_declaration import LoanApplicationDeclaration


def get_by_application_id(db: Session, application_id):
    return (
        db.query(LoanApplicationDeclaration)
        .filter_by(application_id=application_id)
        .first())
