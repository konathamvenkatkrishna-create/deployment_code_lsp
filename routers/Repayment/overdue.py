from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.reminder_log import Reminder_Log


router = APIRouter(prefix="/reminders", tags=["EMI Reminders"])


@router.get("/overdue-summary")
def overdue_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):
    """
    Get overdue summary for current user's ACTIVE loan
    """

    # =====================================================
    # 🔍 GET USER ACTIVE LOAN
    # =====================================================
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == current_user.id,
        LoanApplication.application_status == "ACTIVE"
    ).first()

    if not loan:
        raise HTTPException(404, "No ACTIVE loan found")

    # =====================================================
    # 📊 FETCH ALL OVERDUE RECORDS
    # =====================================================
    overdue_logs = db.query(Reminder_Log).filter(
        Reminder_Log.application_id == loan.id,
        Reminder_Log.overdue_day_count > 0
    ).all()

    if not overdue_logs:
        return {
            "application_id": loan.id,
            "message": "No overdue found",
            "total_overdue_emis": 0,
            "total_penalty": 0
        }

    # =====================================================
    # 📈 AGGREGATION
    # =====================================================
    total_overdue_emis = len(overdue_logs)

    total_penalty = sum(
        float(log.total_penalty_with_gst or 0)
        for log in overdue_logs
    )

    # Latest/highest overdue
    latest = max(overdue_logs, key=lambda x: x.overdue_day_count)

    # =====================================================
    # 📦 RESPONSE
    # =====================================================
    return {
        "application_id": loan.id,

        "summary": {
            "total_overdue_emis": total_overdue_emis,
            "total_penalty": round(total_penalty, 2),
        },

        "latest_overdue": {
            "emi_number": latest.emi_number,
            "overdue_days": latest.overdue_day_count,
            "penalty": float(latest.penalty_amount or 0),
            "penalty_gst": float(latest.penalty_gst or 0),
            "total_penalty": float(latest.total_penalty_with_gst or 0),
            "stage": latest.reminder_stage
        },

        "overdue_list": [
            {
                "emi_number": log.emi_number,
                "overdue_days": log.overdue_day_count,
                "total_penalty": float(log.total_penalty_with_gst or 0)
            }
            for log in overdue_logs
        ]
    }