from sqlalchemy.orm import Session
from typing import Optional

from models.Loan_application.loan_disbursements import LoanDisbursement
from core.enums import DisbursementStatusEnum


class LoanDisbursementRepository:

    # -------------------------------------------------
    # GET BY APPLICATION (ONLY ONE ROW)
    # -------------------------------------------------
    @staticmethod
    def get_by_application_id(
        db: Session,
        application_id: int
    ) -> Optional[LoanDisbursement]:
        return db.query(LoanDisbursement).filter(
            LoanDisbursement.application_id == application_id
        ).first()

    # -------------------------------------------------
    # UPSERT (CREATE OR UPDATE)
    # -------------------------------------------------
    @staticmethod
    def upsert(
        db: Session,
        application_id: int,
        data: dict
    ) -> LoanDisbursement:

        existing = db.query(LoanDisbursement).filter(
            LoanDisbursement.application_id == application_id
        ).first()

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)

            db.commit()
            db.refresh(existing)
            return existing

        new_disbursement = LoanDisbursement(
            application_id=application_id,
            **data
        )

        db.add(new_disbursement)
        db.commit()
        db.refresh(new_disbursement)

        return new_disbursement

    # -------------------------------------------------
    # GET BY RAZORPAY REFERENCE
    # -------------------------------------------------
    @staticmethod
    def get_by_reference(
        db: Session,
        reference_id: str
    ) -> Optional[LoanDisbursement]:
        return db.query(LoanDisbursement).filter(
            LoanDisbursement.payment_reference_id == reference_id
        ).first()

    # -------------------------------------------------
    # SUCCESS CHECK
    # -------------------------------------------------
    @staticmethod
    def get_success_disbursement(
        db: Session,
        application_id: int
    ) -> Optional[LoanDisbursement]:
        return db.query(LoanDisbursement).filter(
            LoanDisbursement.application_id == application_id,
            LoanDisbursement.payment_status == DisbursementStatusEnum.SUCCESS
        ).first()