from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.pagesizes import (
    A4,
    landscape
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import uuid
import os

from core.database import get_db
from core.dependencies import require_roles

from models.Auth.user import User

from models.Profile_KYC.user_profile import (
    UserProfile
)

from models.Loan_application.loan_application import (
    LoanApplication
)

from models.Repayment.emi_scheduled import (
    EMISchedule
)

from core.email_service import (
    EmailService
)

router = APIRouter(
    prefix="/emi-pdf",
    tags=["EMI Schedule"]
)


# =====================================================
# DOWNLOAD EMI PDF
# =====================================================
@router.get("/download")
async def download_emi_pdf(

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    )
):

    # =================================================
    # FETCH USER PROFILE
    # =================================================
    profile = (

        db.query(UserProfile)

        .filter(
            UserProfile.user_id
            == current_user.id
        )

        .first()
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    # =================================================
    # GET LATEST LOAN
    # ACTIVE / CLOSED BOTH SUPPORTED
    # =================================================
    loan = (

        db.query(LoanApplication)

        .filter(
            LoanApplication.user_profile_id
            == profile.user_id
        )

        .order_by(
            LoanApplication.id.desc()
        )

        .first()
    )

    if not loan:

        raise HTTPException(
            status_code=404,
            detail="No loan found"
        )

    # =================================================
    # FETCH EMI DATA
    # =================================================
    emis = (

        db.query(EMISchedule)

        .filter(
            EMISchedule.application_id
            == loan.id
        )

        .order_by(
            EMISchedule.emi_number
        )

        .all()
    )

    if not emis:

        raise HTTPException(
            status_code=404,
            detail="No EMI schedule found"
        )

    # =================================================
    # PDF FILE PATH
    # =================================================
    file_path = (

        f"EMI_{loan.id}_"
        f"{uuid.uuid4().hex}.pdf"
    )

    # =================================================
    # PDF DOCUMENT
    # =================================================
    doc = SimpleDocTemplate(

        file_path,

        pagesize=landscape(A4),

        rightMargin=30,

        leftMargin=30,

        topMargin=25,

        bottomMargin=25
    )

    elements = []

    styles = getSampleStyleSheet()

    # =================================================
    # TITLE
    # =================================================
    elements.append(

        Paragraph(
            "EMI Repayment Schedule",
            styles["Title"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    # =================================================
    # LOAN DETAILS
    # =================================================
    elements.append(

        Paragraph(
            f"Loan ID: {loan.id}",
            styles["Normal"]
        )
    )

    elements.append(

        Paragraph(
            f"Customer: {profile.full_name}",
            styles["Normal"]
        )
    )

    elements.append(

        Paragraph(
            f"Loan Status: {loan.application_status}",
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    # =================================================
    # TABLE HEADERS
    # =================================================
    table_data = [[

        "EMI No",

        "Due Date",

        "Principal",

        "Interest",

        "GST",

        "Total EMI",

        "Status"
    ]]

    total = 0

    # =================================================
    # EMI ROWS
    # =================================================
    for emi in emis:

        table_data.append([

            str(
                emi.emi_number
            ),

            emi.due_date.strftime(
                "%d-%m-%Y"
            ),

            f"{float(emi.principal_component):,.2f}",

            f"{float(emi.interest_component):,.2f}",

            f"{float(emi.gst_amount):,.2f}",

            f"{float(emi.emi_amount):,.2f}",

            emi.status
        ])

        total += float(
            emi.emi_amount
        )

    # =================================================
    # TOTAL ROW
    # =================================================
    table_data.append([

        "",
        "",
        "",
        "",
        "Total",
        f"{total:,.2f}",
        ""
    ])

    # =================================================
    # TABLE
    # =================================================
    table = Table(table_data)

    table.setStyle(TableStyle([

        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.grey
        ),

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.black
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

        (
            "BACKGROUND",
            (0, 1),
            (-1, -1),
            colors.beige
        )

    ]))

    elements.append(table)

    # =================================================
    # BUILD PDF
    # =================================================
    doc.build(elements)

    # =================================================
    # EMAIL PDF
    # =================================================
    try:

        if profile.email:

            with open(file_path, "rb") as f:

                file_bytes = f.read()

            await EmailService.send_email_with_attachment(

                to_email=profile.email,

                subject="EMI Schedule",

                body=(
                    "Please find your "
                    "EMI schedule attached."
                ),

                file_bytes=file_bytes,

                filename=(
                    f"EMI_Schedule_{loan.id}.pdf"
                )
            )

    except Exception as e:

        print(
            f"EMAIL ERROR: {str(e)}"
        )

    # =================================================
    # CLEANUP
    # =================================================
    background_tasks.add_task(
        os.remove,
        file_path
    )

    # =================================================
    # RESPONSE
    # =================================================
    return FileResponse(

        path=file_path,

        filename=(
            f"EMI_Schedule_{loan.id}.pdf"
        ),

        media_type="application/pdf"
    )