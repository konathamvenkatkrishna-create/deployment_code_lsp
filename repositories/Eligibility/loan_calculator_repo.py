from sqlalchemy.orm import Session

from models.Eligibility.loan_calculation import LoanCalculation, LoanCalcStatus
from models.Eligibility.loan_eligibility import LoanEligibility


class LoanCalculationRepository:
    @staticmethod
    def get_eligibility_record(db: Session, user_id: int) -> LoanEligibility | None:
        return (
            db.query(LoanEligibility)
            .filter(LoanEligibility.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> LoanCalculation | None:
        return (
            db.query(LoanCalculation)
            .filter(LoanCalculation.user_id == user_id)
            .first()
        )

    @staticmethod
    def upsert(
        db              : Session,
        user_id         : int,
        requested_amount: float,
        tenure_months   : int,
        eligible_amount : float,
        interest_rate_pa: float,
        monthly_emi     : float,
        total_repayment : float,
        total_interest  : float,
    ) -> LoanCalculation:
        existing = LoanCalculationRepository.get_by_user_id(db, user_id)
        if existing:
            existing.previously_calculated = existing.updated_at

            existing.requested_amount = requested_amount
            existing.tenure_months    = tenure_months
            existing.eligible_amount  = eligible_amount
            existing.interest_rate_pa = interest_rate_pa
            existing.monthly_emi      = monthly_emi
            existing.total_repayment  = total_repayment
            existing.total_interest   = total_interest
            existing.status           = LoanCalcStatus.CHECKED

            db.commit()
            db.refresh(existing)
            return existing

        new_record = LoanCalculation(
            user_id          = user_id,
            requested_amount = requested_amount,
            tenure_months    = tenure_months,
            eligible_amount  = eligible_amount,
            interest_rate_pa = interest_rate_pa,
            monthly_emi      = monthly_emi,
            total_repayment  = total_repayment,
            total_interest   = total_interest,
            status           = LoanCalcStatus.CHECKED,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record