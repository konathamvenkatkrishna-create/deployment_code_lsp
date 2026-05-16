from sqlalchemy.orm import Session
from models.Loan_application.loan_transaction import LoanTransaction


class LoanTransactionRepository:

    @staticmethod
    def create(db: Session, tx: LoanTransaction):
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def update(db: Session, tx: LoanTransaction):
        db.commit()
        db.refresh(tx)
        return tx