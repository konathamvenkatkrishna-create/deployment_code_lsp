import random
from models.Loan_application.loan_application import LoanApplication
def generate_loan_reference_number(db):
    while True:
        ref = f"{random.randint(10_000_000, 99_999_999)}"
        exists = db.query(LoanApplication).filter(
            LoanApplication.reference_number == ref
        ).first()

        if not exists:
            return ref
