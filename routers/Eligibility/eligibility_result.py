from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.Eligibility.eligibility_service import (
    PLATFORM_MAX_LOAN_AMOUNT,
    CREDIT_SCORE_TIERS,
)

from core.database import get_db
from core.dependencies import require_roles

from models.Auth.user import User
from models.Eligibility.loan_eligibility import LoanEligibility

from schemas.Eligibility.eligibility_result import (
    EligibilityResultResponseExtended,
    CreditSummary,
    CreditScoreTier,
)

from utils.eligibility_messages import map_failure_reason

router = APIRouter(
    prefix="/eligibility-result",
    tags=["Loan Eligibility"]
)


@router.get("/me", response_model=EligibilityResultResponseExtended)
def get_eligibility_result(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    """
    Returns the saved eligibility result for the logged-in USER.
    """

    record: LoanEligibility = (
        db.query(LoanEligibility)
        .filter(LoanEligibility.user_id == current_user.id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="No eligibility record found. Please run eligibility check first."
        )

    status = record.eligibility_status
    message = map_failure_reason(record.failure_reason, status)

    # =====================================================
    # CREDIT SUMMARY
    # =====================================================
    credit_summary = CreditSummary(
        currentScore=record.credit_score_used,
        previousScore=record.previous_credit_score_used,
        bureau=record.bureau_name,
    )

    # =====================================================
    # CREDIT TIERS
    # =====================================================
    credit_score_tiers = [
        CreditScoreTier(
            minScore=score,
            maxLoanAmount=amount,
            label=f"₹{amount:,}"
        )
        for score, amount in CREDIT_SCORE_TIERS
    ]

    # =====================================================
    # REJECTED
    # =====================================================
    if status == "REJECTED":
        return EligibilityResultResponseExtended(
            status=status,
            message=message,
            creditSummary=credit_summary,
            creditScoreTiers=credit_score_tiers,
        )

    # =====================================================
    # SUCCESS
    # =====================================================
    max_eligible_amount = min(
        float(record.max_eligible_amount or 0),
        float(PLATFORM_MAX_LOAN_AMOUNT),
    )

    return EligibilityResultResponseExtended(
        status=status,
        message=message,
        maxEligibleAmount=max_eligible_amount,
        creditSummary=credit_summary,
        creditScoreTiers=credit_score_tiers,
        nextStep="EMI_CALCULATION"   # 🔥 IMPORTANT FOR FLOW
    )