from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from dateutil.relativedelta import relativedelta

from models.Loan_application.loan_application import (
    LoanApplication
)

from models.Repayment.emi_scheduled import (
    EMISchedule
)

from core.Loan_calculator import (
    generate_schedule
)


# =====================================================
# CONSTANTS
# =====================================================
GST_RATE = Decimal("0.18")


# =====================================================
# GENERATE EMI SCHEDULE
# =====================================================
def generate_emi_schedule_service(

    current_user_id: int,

    db: Session
):

    # =================================================
    # GET LATEST USER LOAN
    # ACTIVE / CLOSED BOTH SUPPORTED
    # =================================================
    loan = db.query(
        LoanApplication
    ).filter(

        LoanApplication.user_profile_id
        == current_user_id

    ).order_by(
        LoanApplication.id.desc()
    ).first()

    if not loan:

        raise HTTPException(
            status_code=404,
            detail="Loan not found"
        )

    # =================================================
    # FETCH EXISTING EMI SCHEDULE
    # =================================================
    existing_emis = db.query(
        EMISchedule
    ).filter(
        EMISchedule.application_id
        == loan.id
    ).order_by(
        EMISchedule.emi_number
    ).all()

    # =================================================
    # REUSE EXISTING EMI SCHEDULE
    # PREVENT DUPLICATE REGENERATION
    # =================================================
    if existing_emis:

        return {

            "message":
                "Existing EMI schedule fetched successfully",

            "application_id":
                loan.id,

            "loan_status":
                loan.application_status,

            "emi_amount":
                str(existing_emis[0].emi_amount),

            "emis": [

                {
                    "emi_number":
                        e.emi_number,

                    "due_date":
                        str(e.due_date),

                    "opening_principal":
                        str(e.opening_principal),

                    "principal_component":
                        str(e.principal_component),

                    "interest_component":
                        str(e.interest_component),

                    "gst_amount":
                        str(e.gst_amount),

                    "emi_amount":
                        str(e.emi_amount),

                    "closing_principal":
                        str(e.closing_principal),

                    "status":
                        e.status
                }

                for e in existing_emis
            ]
        }

    # =================================================
    # EMI START DATE
    # =================================================
    first_emi_date = (
        loan.created_at
        + relativedelta(months=1)
    ).date()

    # =================================================
    # INPUTS
    # =================================================
    principal = Decimal(
        str(loan.approved_amount)
    )

    annual_rate = Decimal(
        str(loan.interest_rate)
    )

    tenure = loan.requested_tenure_months

    # =================================================
    # GENERATE EMI SCHEDULE
    # =================================================
    try:

        schedule_data = generate_schedule(

            principal=principal,

            annual_rate=annual_rate,

            tenure=tenure,

            first_emi_date=first_emi_date
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    generated_emis = []

    # =================================================
    # CREATE EMI RECORDS
    # =================================================
    for item in schedule_data:

        # =============================================
        # SAFE DECIMAL
        # =============================================
        interest = Decimal(
            str(item["interest_component"])
        )

        emi_base = Decimal(
            str(item["emi_amount"])
        )

        # =============================================
        # GST CALCULATION
        # =============================================
        gst_amount = (
            interest * GST_RATE
        ).quantize(
            Decimal("0.01")
        )

        # =============================================
        # TOTAL EMI
        # =============================================
        total_emi = (
            emi_base + gst_amount
        ).quantize(
            Decimal("0.01")
        )

        emi = EMISchedule(

            application_id=
                loan.id,

            emi_number=
                item["emi_number"],

            due_date=
                item["due_date"],

            opening_principal=
                item["opening_principal"],

            principal_component=
                item["principal_component"],

            interest_component=
                item["interest_component"],

            gst_amount=
                gst_amount,

            emi_amount=
                total_emi,

            closing_principal=
                item["closing_principal"],

            status=
                "DUE"
        )

        db.add(emi)

        generated_emis.append(emi)

    db.commit()

    # =================================================
    # RESPONSE
    # =================================================
    return {

        "message":
            f"{tenure} EMI's generated successfully",

        "application_id":
            loan.id,

        "loan_status":
            loan.application_status,

        "first_emi_date":
            str(first_emi_date),

        "emi_amount":
            str(generated_emis[0].emi_amount),

        "emis": [

            {
                "emi_number":
                    e.emi_number,

                "due_date":
                    str(e.due_date),

                "opening_principal":
                    str(e.opening_principal),

                "principal_component":
                    str(e.principal_component),

                "interest_component":
                    str(e.interest_component),

                "gst_amount":
                    str(e.gst_amount),

                "emi_amount":
                    str(e.emi_amount),

                "closing_principal":
                    str(e.closing_principal),

                "status":
                    e.status
            }

            for e in generated_emis
        ]
    }