from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.Repayment.emi_scheduled import (
    EMISchedule
)

from models.Loan_application.loan_application import (
    LoanApplication
)

from schemas.Repayment.prepayment_schema import (
    PrepayResponse,
    PrepayEMIItem
)


# =====================================================
# CONFIG
# =====================================================
PREPAY_PENALTY_RATE = Decimal("0.02")

GST_RATE = Decimal("0.18")


# =====================================================
# SAFE DECIMAL
# =====================================================
def safe_decimal(value):

    return Decimal(
        str(value or 0)
    )


# =====================================================
# PREPAY SUMMARY
# =====================================================
def process_prepay(

    db: Session,

    user_id: int,
):
    """
    =====================================================
    PREPAY SUMMARY ONLY
    =====================================================

    DOES NOT:
    - initiate payment
    - create transaction
    - update EMI
    - update loan

    Existing payment API + webhook
    handles payment execution.

    =====================================================
    CALCULATES
    =====================================================

    - all unpaid EMIs
    - principal outstanding
    - interest outstanding
    - GST outstanding
    - prepay penalty
    - penalty GST
    - total payable
    """

    # =================================================
    # GET ACTIVE LOAN
    # =================================================
    loan = db.query(
        LoanApplication
    ).filter(

        LoanApplication.user_profile_id
        == user_id,

        LoanApplication.application_status
        == "ACTIVE"

    ).first()

    if not loan:

        raise HTTPException(

            status_code=404,

            detail="No ACTIVE loan found"
        )

    application_id = loan.id

    # =================================================
    # FETCH ALL PENDING EMIs
    # =================================================
    emis = db.query(
        EMISchedule
    ).filter(

        EMISchedule.application_id
        == application_id,

        EMISchedule.status.in_([
            "DUE",
            "PENDING",
            "UNPAID",
            "OVERDUE"
        ])

    ).order_by(
        EMISchedule.due_date
    ).all()

    if not emis:

        raise HTTPException(

            status_code=404,

            detail="No pending EMIs found"
        )

    # =================================================
    # EMI TOTALS
    # =================================================
    total_emi = sum(

        safe_decimal(
            e.emi_amount
        )

        for e in emis
    )

    total_principal = sum(

        safe_decimal(
            e.principal_component
        )

        for e in emis
    )

    total_interest = sum(

        safe_decimal(
            e.interest_component
        )

        for e in emis
    )

    total_gst = sum(

        safe_decimal(
            e.gst_amount
        )

        for e in emis
    )

    # =================================================
    # PREPAY PENALTY
    # =================================================
    prepay_penalty = (

        total_principal
        * PREPAY_PENALTY_RATE

    ).quantize(
        Decimal("0.01")
    )

    # =================================================
    # PENALTY GST
    # =================================================
    penalty_gst = (

        prepay_penalty
        * GST_RATE

    ).quantize(
        Decimal("0.01")
    )

    # =================================================
    # FINAL PAYABLE
    # =================================================
    total_payable = (

        total_emi
        + prepay_penalty
        + penalty_gst

    ).quantize(
        Decimal("0.01")
    )

    # =================================================
    # EMI ITEMS
    # =================================================
    emi_items = [

        PrepayEMIItem(

            emi_number=
                e.emi_number,

            due_date=
                e.due_date,

            emi_amount=
                safe_decimal(
                    e.emi_amount
                ),

            principal_component=
                safe_decimal(
                    e.principal_component
                ),

            interest_component=
                safe_decimal(
                    e.interest_component
                ),

            gst_amount=
                safe_decimal(
                    e.gst_amount
                )
        )

        for e in emis
    ]

    # =================================================
    # RESPONSE
    # =================================================
    return PrepayResponse(

        application_id=
            application_id,

        total_emis_selected=
            len(emis),

        emis=
            emi_items,

        total_emi_amount=
            total_emi,

        total_principal=
            total_principal,

        total_interest=
            total_interest,

        total_gst=
            total_gst,

        prepay_penalty=
            prepay_penalty,

        penalty_gst=
            penalty_gst,

        total_payable=
            total_payable
    )