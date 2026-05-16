from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks
)

from fastapi.responses import (
    StreamingResponse
)

from sqlalchemy.orm import Session

from io import BytesIO

from decimal import Decimal

from datetime import datetime

from reportlab.lib.pagesizes import (
    A4,
    landscape
)

from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from core.database import get_db

from core.dependencies import (
    require_roles
)

from core.email_service import (
    EmailService
)

from models.Auth.user import User

from models.Loan_application.loan_application import (
    LoanApplication
)

from models.Repayment.payments import (
    Payment_Transaction
)

from models.Repayment.emi_scheduled import (
    EMISchedule
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(
    prefix="/payments",
    tags=["Payment History"]
)


# =====================================================
# GST
# =====================================================
GST_RATE = Decimal("0.18")


# =====================================================
# FORMATTER
# =====================================================
def _fmt(val):

    try:

        return f"{float(val):,.2f}"

    except Exception:

        return str(val)


# =====================================================
# EMI PARSER
# =====================================================
def _parse_emi_numbers(
    emi_number
):

    if isinstance(emi_number, int):

        return [emi_number]

    if isinstance(emi_number, str):

        return [
            int(e.strip())
            for e in emi_number.split(",")
            if e.strip().isdigit()
        ]

    return []


# =====================================================
# PAYMENT HISTORY PDF
# =====================================================
@router.get("/history/receipt/pdf")
async def download_payment_history_pdf(

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    )
):

    # =====================================================
    # USER PROFILE CHECK
    # =====================================================
    profile = getattr(
        current_user,
        "profile",
        None
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    # =====================================================
    # FETCH LOAN
    # =====================================================
    loan = db.query(
        LoanApplication
    ).filter(
        LoanApplication.user_profile_id
        == profile.user_id
    ).order_by(
        LoanApplication.id.desc()
    ).first()

    if not loan:

        raise HTTPException(
            status_code=404,
            detail="No loan found"
        )

    application_id = loan.id

    # =====================================================
    # FETCH PAYMENTS
    # =====================================================
    payments = db.query(
        Payment_Transaction
    ).filter(
        Payment_Transaction.application_id
        == application_id
    ).order_by(
        Payment_Transaction.created_at
    ).all()

    if not payments:

        raise HTTPException(
            status_code=404,
            detail="No payment records found"
        )

    # =====================================================
    # FETCH EMIs
    # =====================================================
    emis = db.query(
        EMISchedule
    ).filter(
        EMISchedule.application_id
        == application_id
    ).all()

    emi_map = {
        e.emi_number: e
        for e in emis
    }

    # =====================================================
    # PDF BUFFER
    # =====================================================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4)
    )

    styles = getSampleStyleSheet()

    elements = []

    # =====================================================
    # TITLE
    # =====================================================
    elements.append(
        Paragraph(
            "Payment History Receipt",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Paragraph(
            f"Application ID: {application_id}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Customer Name: "
            f"{profile.full_name}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 12)
    )

    # =====================================================
    # TABLE
    # =====================================================
    table_data = [[
        "Txn ID",
        "EMI",
        "Principal",
        "Interest",
        "GST",
        "Total EMI",
        "Paid",
        "Mode",
        "Date"
    ]]

    total_paid = Decimal("0")

    # =====================================================
    # PAYMENT LOOP
    # =====================================================
    for p in payments:

        principal_total = Decimal("0")

        interest_total = Decimal("0")

        for emi in _parse_emi_numbers(
            p.emi_number
        ):

            emi_obj = emi_map.get(emi)

            if emi_obj:

                principal_total += Decimal(
                    str(
                        emi_obj.principal_component
                        or 0
                    )
                )

                interest_total += Decimal(
                    str(
                        emi_obj.interest_component
                        or 0
                    )
                )

        total_emi = (
            principal_total
            + interest_total
        )

        gst = (
            interest_total
            * GST_RATE
        )

        amount = Decimal(
            str(
                p.amount_paid
                or 0
            )
        )

        total_paid += amount

        table_data.append([
            str(
                p.transaction_id
                or "-"
            ),

            str(
                p.emi_number
                or "-"
            ),

            _fmt(principal_total),

            _fmt(interest_total),

            _fmt(gst),

            _fmt(total_emi),

            _fmt(amount),

            str(
                p.payment_mode
                or "-"
            ),

            p.created_at.strftime(
                "%d-%m-%Y"
            )
            if p.created_at
            else "-"
        ])

    # =====================================================
    # TOTAL ROW
    # =====================================================
    table_data.append([
        "",
        "",
        "",
        "",
        "",
        "TOTAL",
        _fmt(total_paid),
        "",
        ""
    ])

    # =====================================================
    # CREATE TABLE
    # =====================================================
    table = Table(
        table_data
    )

    table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                10
            ),
        ])
    )

    elements.append(
        table
    )

    # =====================================================
    # BUILD PDF
    # =====================================================
    doc.build(elements)

    buffer.seek(0)

    pdf_bytes = buffer.getvalue()

    # =====================================================
    # EMAIL PDF
    # =====================================================
    if (
        hasattr(current_user, "profile")
        and current_user.profile
        and current_user.profile.email
    ):

        try:

            await EmailService.send_email_with_attachment(

                to_email=current_user.profile.email,

                subject="Payment Receipt",

                body=(
                    "Your payment receipt "
                    "is attached."
                ),

                file_bytes=pdf_bytes,

                filename=(
                    f"payment_"
                    f"{application_id}.pdf"
                )
            )

        except Exception as e:

            print(
                f"Email failed: {str(e)}"
            )

    # =====================================================
    # RETURN PDF
    # =====================================================
    return StreamingResponse(

        BytesIO(pdf_bytes),

        media_type="application/pdf",

        headers={
            "Content-Disposition":
                f"attachment; "
                f"filename=payment_"
                f"{application_id}.pdf"
        }
    )