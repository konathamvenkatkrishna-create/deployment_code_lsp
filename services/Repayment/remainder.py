
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from models.Repayment.emi_scheduled import EMISchedule
from models.Loan_application.loan_application import LoanApplication
from models.Auth.user import User
from models.Repayment.reminder_log import Reminder_Log

from core.email_service import EmailService


OVERDUE_PENALTY_RATE = Decimal("0.02")


# =====================================================
# ✅ NOTIFICATION SERVICE (FIXED)
# =====================================================
class ReminderService:

    @staticmethod
    def send_sms(mobile, message):
        print(f"📱 SMS → {mobile}: {message}")

    @staticmethod
    def send_push(user_id, message):
        print(f"📲 PUSH → User {user_id}: {message}")


# =====================================================
# MAIN LOGIC
# =====================================================
async def process_emi_reminders(user_id: int, db: Session):

    today = date.today()

    # =====================================================
    # 🔍 GET ACTIVE LOAN
    # =====================================================
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        return {"message": "No ACTIVE loan found"}

    # =====================================================
    # 🔍 GET USER DETAILS
    # =====================================================
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == loan.id,
        EMISchedule.status != "PAID"
    ).all()

    if not emis:
        return {"message": "No pending EMIs"}

    triggered = []

    # =====================================================
    # 🔄 PROCESS EACH EMI
    # =====================================================
    for emi in emis:

        due_date = emi.due_date
        days_left = (due_date - today).days

        message = None
        stage = None

        # 📅 Upcoming reminders
        if days_left in [7, 3, 1]:
            message = f"Reminder: EMI ₹{emi.emi_amount} due on {due_date} ({days_left} day(s) left)"
            stage = f"PRE_DUE_{days_left}"

        # 📅 Due today
        elif days_left == 0:
            message = f"EMI ₹{emi.emi_amount} is due TODAY ({due_date})"
            stage = "DUE_TODAY"

        # 🔴 Overdue
        elif days_left < 0:
            overdue_days = abs(days_left)

            penalty = (
                Decimal(str(emi.emi_amount)) * OVERDUE_PENALTY_RATE
            ).quantize(Decimal("0.01"))

            message = (
                f"Overdue: EMI ₹{emi.emi_amount} due on {due_date}. "
                f"{overdue_days} days late. Penalty ₹{penalty}"
            )
            stage = f"OVERDUE_{overdue_days}"

        if not message:
            continue

        # =====================================================
        # 🚫 DUPLICATE CHECK
        # =====================================================
        existing = db.query(Reminder_Log).filter(
            Reminder_Log.application_id == loan.id,
            Reminder_Log.emi_number == emi.emi_number,
            Reminder_Log.reminder_stage == stage
        ).first()

        if existing:
            continue

        # =====================================================
        # 📩 SEND NOTIFICATIONS (FIXED)
        # =====================================================
        if user.email:
            await EmailService.send_email(
                to_email=user.email,
                subject="EMI Reminder",
                body=message
            )

        if user.mobile_number:
            ReminderService.send_sms(user.mobile_number, message)

        ReminderService.send_push(user_id, message)

        # =====================================================
        # 📝 SAVE LOG
        # =====================================================
        log = Reminder_Log(
            application_id=loan.id,
            emi_number=emi.emi_number,
            overdue_day_count=abs(days_left) if days_left < 0 else 0,
            reminder_stage=stage,
            message=message
        )

        db.add(log)

        triggered.append({
            "emi_number": emi.emi_number,
            "due_date": str(emi.due_date),
            "stage": stage,
            "days_left": days_left
        })

    db.commit()

    return {
        "application_id": loan.id,
        "total_reminders_sent": len(triggered),
        "details": triggered
    }


# =====================================================
# ROUTER CALLABLE
# =====================================================
async def trigger_manual(user_id: int, db: Session):
    return await process_emi_reminders(user_id, db)

