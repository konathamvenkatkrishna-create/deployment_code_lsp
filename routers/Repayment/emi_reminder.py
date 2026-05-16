from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.Auth.user import User
from core.database import get_db
from core.dependencies import require_roles
from models.Loan_application import LoanApplication
from models.Repayment import Reminder_Log
from services.Repayment.remainder import ReminderService
from models.Repayment.emi_scheduled import EMISchedule
from core.email_service import EmailService

router = APIRouter(prefix="/reminders", tags=["EMI Reminders"])


@router.post("/manual")
async def trigger_manual(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["USER"])) 
):
    result = await ReminderService.process(user.id, db)

    if "message" in result:
        raise HTTPException(status_code=404, detail=result["message"])

    # ✅ GET LOAN
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user.id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(status_code=404, detail="No ACTIVE loan")

    # ✅ GET USER EMAIL
    
    user_data = db.query(User).filter(User.user_id == loan.user_id).first()

    if not user_data or not user_data.email:
        raise HTTPException(status_code=404, detail="User email not found")

    to_email = user_data.email

    # ✅ GET EMIs
   
    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id
    ).order_by(EMISchedule.emi_number).all()

    if not emis:
        raise HTTPException(status_code=404, detail="No EMI schedule found")

    # ============================
    # ✅ GENERATE EMI PDF
    # ============================
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.lib.pagesizes import A4

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    table_data = [["EMI No", "Due Date", "Amount"]]

    for emi in emis:
        table_data.append([
            str(emi.emi_number),
            str(emi.due_date),
            str(float(emi.emi_amount))
        ])

    table = Table(table_data)
    doc.build([table])
    buffer.seek(0)

    pdf_bytes = buffer.getvalue()

    # ============================
    # ✅ SEND EMAILS
    # ============================
    
    import asyncio

    # 👉 Send EMI Schedule PDF
    asyncio.create_task(
        EmailService.send_emi_schedule(
            to_email=to_email,
            pdf_bytes=pdf_bytes,
            loan_id=str(loan.id)
        )
    )

    # 👉 Send EMI Reminder Emails
    for emi in emis:
        if emi.status == "DUE":
            asyncio.create_task(
                EmailService.send_emi_reminder(
                    to_email=to_email,
                    emi_no=emi.emi_number,
                    due_date=str(emi.due_date),
                    amount=float(emi.emi_amount)
                )
            )

    return {
        "message": "EMI reminder + schedule sent successfully",
        "email": to_email
    }


@router.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    user = Depends(require_roles(["USER"]))
):
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user.id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(status_code=404, detail="No ACTIVE loan")

    logs = db.query(Reminder_Log).filter(
        Reminder_Log.application_id == loan.id
    ).all()

    return logs