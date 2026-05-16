
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from decimal import Decimal
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from models.Loan_application.loan_application import LoanApplication
from models.Repayment.emi_scheduled import EMISchedule
from models.Repayment.payments import Payment_Transaction
from models.Auth.lender import Lender


router = APIRouter(prefix="/payments", tags=["Loan Documents"])


# =====================================================
# 🔒 SECURE FETCH (USER BASED)
# =====================================================
def get_user_loan(db: Session, user_id: int):

    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id
    ).order_by(LoanApplication.id.desc()).first()

    if not loan:
        raise HTTPException(404, "Loan not found")

    return loan


# =====================================================
# LOAN CLOSURE PDF (FINAL)
# =====================================================
@router.get("/loan-closure/pdf")
def loan_closure_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):

    loan = get_user_loan(db, current_user.id)

    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id
    ).all()

    payments = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == loan.id
    ).all()

    lender = db.query(Lender).filter(
        Lender.id == loan.lender_id
    ).first()

    # 🚨 VALIDATION
    unpaid = [e for e in emis if e.status != "PAID"]
    if unpaid:
        raise HTTPException(400, "Loan not fully closed")

    # 📊 CALCULATIONS
    total_paid = sum(Decimal(str(p.amount_paid or 0)) for p in payments)
    total_interest = sum(Decimal(str(e.interest_component)) for e in emis)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    # TITLE
    elements.append(Paragraph("LOAN CLOSURE CERTIFICATE"))
    elements.append(Spacer(1, 10))

    # TABLE DATA
    data = [
        ["Application ID", loan.id],
        ["Lender", lender.company_name if lender else "N/A"],
        ["Loan Status", "CLOSED"],
        ["Total Paid", f"₹ {float(total_paid):,.2f}"],
        ["Total Interest", f"₹ {float(total_interest):,.2f}"],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=closure_{loan.id}.pdf"}
    )


# =====================================================
# CREDIT REPORT PDF (FINAL)
# =====================================================
@router.get("/credit-report/pdf")
def credit_report_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):

    loan = get_user_loan(db, current_user.id)

    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id
    ).all()

    payments = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == loan.id
    ).all()

    lender = db.query(Lender).filter(
        Lender.id == loan.lender_id
    ).first()

    total_paid = sum(Decimal(str(p.amount_paid or 0)) for p in payments)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    elements.append(Paragraph("CREDIT REPORT"))
    elements.append(Spacer(1, 10))

    data = [
        ["Application ID", loan.id],
        ["Lender", lender.company_name if lender else "N/A"],
        ["Total Paid", f"₹ {float(total_paid):,.2f}"],
        ["Status", loan.application_status],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=credit_{loan.id}.pdf"}
    )

