from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from models.Repayment.emi_scheduled import EMISchedule
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.ndc_generation import NoDueCertificate

from utils.pdf.ndc_generator import generate_ndc_pdf


def generate_ndc(db: Session, user_id: int):

    # =====================================================
    # 🔍 GET CLOSED LOAN
    # =====================================================
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == "CLOSED"
    ).first()

    if not loan:
        raise HTTPException(404, "No CLOSED loan found")

    application_id = loan.id

    # =====================================================
    # 🔐 VERIFY ALL EMIs PAID
    # =====================================================
    unpaid = db.query(EMISchedule).filter(
        EMISchedule.application_id == application_id,
        EMISchedule.status != "PAID"
    ).first()

    if unpaid:
        raise HTTPException(400, "Loan not fully paid")

    # =====================================================
    # 📄 CHECK EXISTING
    # =====================================================
    existing = db.query(NoDueCertificate).filter(
        NoDueCertificate.application_id == application_id
    ).first()

    if existing:
        return {
            "message": "Already generated",
            "pdf_url": existing.pdf_url
        }

    # =====================================================
    # 📄 GENERATE PDF
    # =====================================================
    file_path = f"media/ndc/ndc_{application_id}.pdf"

    generate_ndc_pdf(
        file_path=file_path,
        borrower_name=str(loan.user_profile_id),  # replace with actual name
        loan_id=loan.id,
        application_id=loan.id
    )

    # =====================================================
    # 💾 SAVE
    # =====================================================
    ndc = NoDueCertificate(
        application_id=application_id,
        loan_id=application_id,
        pdf_url=file_path,
        created_at=datetime.utcnow()
    )

    db.add(ndc)
    db.commit()
    db.refresh(ndc)

    return {
        "message": "NDC generated successfully",
        "pdf_url": file_path
    }