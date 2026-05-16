from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional

from models.Eligibility.loan_eligibility import LoanEligibility


class EligibilityRepository:

    # ---------------------------------------------------
    # GET LATEST ELIGIBILITY BY USER
    # ---------------------------------------------------
    @staticmethod
    def get_latest_by_user(
        db: Session,
        user_id: int
    ) -> Optional[LoanEligibility]:

        return (
            db.query(LoanEligibility)
            .filter(LoanEligibility.user_id == user_id)
            .order_by(LoanEligibility.latest_checked_at.desc())
            .first()
        )

    # ---------------------------------------------------
    # SAVE OR UPDATE ELIGIBILITY
    # ---------------------------------------------------
    @staticmethod
    def save_or_update_eligibility(
        db: Session,
        user_id: int,
        eligibility_status: str,
        credit_profile_id: int = None,
        income_used: float = None,
        existing_emi: float = None,
        proposed_emi: float = None,
        foir_ratio: float = None,
        credit_score_used: int = None,
        bureau_name: str = None,
        max_eligible_amount: float = None,
        max_eligible_emi: float = None,
        failure_reason: str = None,
    ) -> LoanEligibility:

        now = datetime.utcnow()

        eligibility = (
            db.query(LoanEligibility)
            .filter(LoanEligibility.user_id == user_id)
            .first()
        )

        if not eligibility:
            eligibility = LoanEligibility(
                user_id=user_id,
                previous_credit_score_used=None,
                previously_checked_at=None,
                latest_checked_at=now,
            )
            db.add(eligibility)

        else:
            if (
                eligibility.credit_score_used is not None
                and eligibility.credit_score_used != credit_score_used
            ):
                eligibility.previous_credit_score_used = (
                    eligibility.credit_score_used
                )

            eligibility.previously_checked_at = eligibility.latest_checked_at
            eligibility.latest_checked_at = now

        eligibility.credit_profile_id = credit_profile_id
        eligibility.income_used = income_used
        eligibility.existing_emi = existing_emi
        eligibility.proposed_emi = proposed_emi
        eligibility.foir_ratio = foir_ratio
        eligibility.credit_score_used = credit_score_used
        eligibility.bureau_name = bureau_name
        eligibility.max_eligible_amount = max_eligible_amount
        eligibility.max_eligible_emi = max_eligible_emi
        eligibility.eligibility_status = eligibility_status
        eligibility.failure_reason = failure_reason

        db.commit()
        db.refresh(eligibility)

        return eligibility