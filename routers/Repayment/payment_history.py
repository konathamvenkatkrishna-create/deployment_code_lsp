from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User

from models.Repayment.payments import Payment_Transaction
from models.Repayment.emi_scheduled import EMISchedule
from models.Loan_application.loan_application import LoanApplication


router = APIRouter(prefix="/payments", tags=["Payment-History"])


GST_RATE         = Decimal("0.18")
PREPAY_RATE      = Decimal("0.02")
FORECLOSURE_RATE = Decimal("0.04")


# =====================================================
# SCHEMAS
# =====================================================
class PaymentDetail(BaseModel):
    payment_id: int
    transaction_id: str
    emi_number: Optional[str]

    principal: float
    interest: float
    total_emi_amount: float

    gst_on_interest: float
    foreclosure_charges: float
    prepay_charges: float
    gst_on_charges: float

    total_amount_paid: float

    payment_mode: Optional[str]
    payment_option: Optional[str]
    payment_date: Optional[datetime]


class PaymentHistoryResponse(BaseModel):
    application_id: int
    total_payments: int
    total_amount_paid: float
    payment_details: List[PaymentDetail]


# =====================================================
# HELPER
# =====================================================
def parse_emi_numbers(emi_number):
    if not emi_number:
        return []
    if isinstance(emi_number, int):
        return [emi_number]
    if isinstance(emi_number, str):
        return [int(x.strip()) for x in emi_number.split(",") if x.strip().isdigit()]
    return []


# =====================================================
# ✅ PAYMENT HISTORY ONLY
# =====================================================
@router.get("/history", response_model=PaymentHistoryResponse)
def get_payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER"))
):

    # 🔐 Get user loan
    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == current_user.id
    ).order_by(LoanApplication.id.desc()).first()

    if not loan:
        raise HTTPException(404, "No loan found")

    application_id = loan.id

    payments = db.query(Payment_Transaction).filter(
        Payment_Transaction.application_id == application_id
    ).order_by(Payment_Transaction.created_at).all()

    if not payments:
        raise HTTPException(404, "No payment records found")

    # 🔥 Optimization (avoid N+1)
    emis = db.query(EMISchedule).filter(
        EMISchedule.application_id == application_id
    ).all()

    emi_map = {e.emi_number: e for e in emis}

    payment_rows = []
    total_paid = Decimal("0")

    for p in payments:

        emi_numbers = parse_emi_numbers(p.emi_number)

        principal_total = Decimal("0")
        interest_total  = Decimal("0")

        for emi_num in emi_numbers:
            emi = emi_map.get(emi_num)
            if emi:
                principal_total += Decimal(str(emi.principal_component or 0))
                interest_total  += Decimal(str(emi.interest_component or 0))

        amount_paid = Decimal(str(p.amount_paid or 0))
        total_paid += amount_paid

        total_emi_amount = principal_total + interest_total
        gst_on_interest  = (interest_total * GST_RATE).quantize(Decimal("0.01"))

        foreclosure_charges = Decimal("0")
        prepay_charges      = Decimal("0")
        gst_on_charges      = Decimal("0")

        option = (p.payment_option or "").lower()

        if option == "foreclosure":
            foreclosure_charges = total_emi_amount * FORECLOSURE_RATE
            gst_on_charges = foreclosure_charges * GST_RATE

        elif option == "prepay":
            prepay_charges = total_emi_amount * PREPAY_RATE
            gst_on_charges = prepay_charges * GST_RATE

        payment_rows.append(PaymentDetail(
            payment_id          = p.payment_id,
            transaction_id      = str(p.transaction_id or "N/A"),
            emi_number          = p.emi_number,

            principal           = round(float(principal_total), 2),
            interest            = round(float(interest_total), 2),
            total_emi_amount    = round(float(total_emi_amount), 2),

            gst_on_interest     = round(float(gst_on_interest), 2),
            foreclosure_charges = round(float(foreclosure_charges), 2),
            prepay_charges      = round(float(prepay_charges), 2),
            gst_on_charges      = round(float(gst_on_charges), 2),

            total_amount_paid   = round(float(amount_paid), 2),

            payment_mode        = p.payment_mode,
            payment_option      = p.payment_option,
            payment_date        = p.created_at,
        ))

    return PaymentHistoryResponse(
        application_id    = application_id,
        total_payments    = len(payment_rows),
        total_amount_paid = round(float(total_paid), 2),
        payment_details   = payment_rows,
    )