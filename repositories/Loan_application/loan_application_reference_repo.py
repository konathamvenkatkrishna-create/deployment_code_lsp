from sqlalchemy.orm import Session
from models.Loan_application.loan_application_references import LoanApplicationReference
from models.Loan_application.loan_application import LoanApplication


class LoanApplicationReferenceRepository:

    # -------------------------------------------------
    # Get all references by application
    # -------------------------------------------------
    @staticmethod
    def get_by_application_id(db: Session, application_id: int):
        return (
            db.query(LoanApplicationReference)
            .filter(LoanApplicationReference.application_id == application_id)
            .all()
        )

    # -------------------------------------------------
    # Get single reference by ID
    # -------------------------------------------------
    @staticmethod
    def get_by_id(db: Session, reference_id: int):
        return (
            db.query(LoanApplicationReference)
            .filter(LoanApplicationReference.id == reference_id)
            .first()
        )

    # -------------------------------------------------
    # 🔥 REQUIRED FOR OTP FLOW
    # Get reference by USER + MOBILE NUMBER
    # -------------------------------------------------
    @staticmethod
    def get_by_user_and_mobile_number(
        db: Session,
        user_id: int,
        mobile_number: str
    ):
        return (
            db.query(LoanApplicationReference)
            .join(
                LoanApplication,
                LoanApplicationReference.application_id == LoanApplication.id
            )
            .filter(
                LoanApplication.user_profile_id == user_id,
                LoanApplicationReference.mobile_number == mobile_number
            )
            .first()
        )

    # -------------------------------------------------
    # Create reference
    # -------------------------------------------------
    @staticmethod
    def create(db: Session, reference: LoanApplicationReference):
        db.add(reference)
        db.commit()
        db.refresh(reference)
        return reference

    # -------------------------------------------------
    # Delete all references for an application
    # -------------------------------------------------
    @staticmethod
    def delete_by_application_id(db: Session, application_id: int):
        db.query(LoanApplicationReference)\
            .filter(LoanApplicationReference.application_id == application_id)\
            .delete()
        db.commit()