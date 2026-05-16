from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, date
import time

from models.Repayment.emi_scheduled import EMISchedule
from models.Repayment.lender_payment_details import LenderPaymentDetails
from models.Loan_application.loan_application import LoanApplication
from models.Repayment.payments import Payment_Transaction   

from core.enums import LoanApplicationStatus

from schemas.Repayment.auto_debit_schema import (
    PaymentModeEnum,
    PaymentOptionEnum,
    PaymentResponse,
    OverdueResponse,
    OverdueEMIItem,
    NoOverdueResponse,
    LenderUPIDetails,
    LenderBankTransferDetails,
    LenderCreditCardDetails,
)

OVERDUE_PENALTY_RATE = Decimal("0.02")
PENALTY_GST_RATE     = Decimal("0.18")


# =====================================================
# HELPERS
# =====================================================
def _get_next_due_emi(db: Session, application_id: int) -> EMISchedule:
    emi = (
        db.query(EMISchedule)
        .filter(
            and_(
                EMISchedule.application_id == application_id,
                EMISchedule.status == "DUE",
            )
        )
        .order_by(EMISchedule.emi_number)
        .first()
    )
    if not emi:
        raise HTTPException(status_code=404, detail="No pending EMIs found.")
    return emi


def _get_all_due_emis(db: Session, application_id: int):
    return (
        db.query(EMISchedule)
        .filter(
            and_(
                EMISchedule.application_id == application_id,
                EMISchedule.status == "DUE",
            )
        )
        .order_by(EMISchedule.emi_number)
        .all()
    )


def _get_overdue_emis(db: Session, application_id: int):
    today = date.today()
    return (
        db.query(EMISchedule)
        .filter(
            and_(
                EMISchedule.application_id == application_id,
                EMISchedule.status == "DUE",
                EMISchedule.due_date < today,
            )
        )
        .order_by(EMISchedule.emi_number)
        .all()
    )


# =====================================================
# ✅ CORRECT: FETCH PAYMENT DETAILS DIRECTLY
# =====================================================
def _get_lender_payment_details(
    db: Session,
    application_id: int,
    payment_mode: PaymentModeEnum
):
    loan = db.query(LoanApplication).filter(
        LoanApplication.id == application_id
    ).first()

    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if not loan.lender_id:
        raise HTTPException(status_code=404, detail="Lender not assigned")

    payment = db.query(LenderPaymentDetails).filter(
        LenderPaymentDetails.lender_id == loan.lender_id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Lender payment details not found")

    # =========================
    # RETURN BASED ON MODE
    # =========================
    if payment_mode == PaymentModeEnum.upi:
        if not payment.upi_id:
            raise HTTPException(status_code=400, detail="UPI not configured")

        return LenderUPIDetails(
            lender_upi=payment.upi_id,
            lender_account_holder_name="Lender"
        )

    elif payment_mode == PaymentModeEnum.bank_transfer:
        if not payment.account_number or not payment.ifsc:
            raise HTTPException(status_code=400, detail="Bank details not configured")

        return LenderBankTransferDetails(
            lender_account_holder_name="Lender",
            lender_account_number=payment.account_number,
            ifsc=payment.ifsc,
            lender_bank_name=payment.bank_name,
        )

    elif payment_mode == PaymentModeEnum.credit_card:
        if not payment.card_number:
            raise HTTPException(status_code=400, detail="Card details not configured")

        return LenderCreditCardDetails(
            lender_account_holder_name="Lender",
            lender_card_number=f"**** **** **** {payment.card_number[-4:]}",
            lender_card_type=payment.card_type,
            lender_expiry=payment.expiry,
        )


def _save_payment(
    db: Session,
    application_id: int,
    emi_number: str,
    amount_paid: Decimal,
    payment_mode: PaymentModeEnum,
    payment_option: PaymentOptionEnum,
    due_date
):
    txn = Payment_Transaction(
        application_id=application_id,
        emi_number=emi_number,
        amount_paid=amount_paid,
        payment_mode=payment_mode.value,
        payment_option=payment_option.value,
        transaction_id=str(int(time.time() * 1000))[-12:],
        created_at=datetime.combine(due_date, datetime.min.time())
    )
    db.add(txn)
    db.flush()
    return txn


# =====================================================
# MAIN SERVICE
# =====================================================
def process_auto_debit(
    db: Session,
    user_id: int,
    payment_mode: PaymentModeEnum,
    payment_option: PaymentOptionEnum
):

    loan = db.query(LoanApplication).filter(
        LoanApplication.user_profile_id == user_id,
        LoanApplication.application_status == LoanApplicationStatus.ACTIVE
    ).first()

    if not loan:
        raise HTTPException(status_code=404, detail="No ACTIVE loan found")

    application_id = loan.id
    today = date.today()

    # =====================================================
    # 🔴 OVERDUE CASE
    # =====================================================
    if payment_option == PaymentOptionEnum.overdue:
        overdue_emis = _get_overdue_emis(db, application_id)

        if not overdue_emis:
            return NoOverdueResponse(
                application_id=application_id,
                message="No overdue EMIs",
                overdue_count=0,
                penalty=Decimal("0.00"),
                penalty_gst=Decimal("0.00"),
                total_payable=Decimal("0.00"),
            )

        total = sum(Decimal(str(e.emi_amount)) for e in overdue_emis)

        penalty = (total * OVERDUE_PENALTY_RATE).quantize(Decimal("0.01"))
        gst = (penalty * PENALTY_GST_RATE).quantize(Decimal("0.01"))

        return OverdueResponse(
            application_id=application_id,
            overdue_count=len(overdue_emis),
            total_emi_amount=total,
            penalty=penalty,
            penalty_gst=gst,
            total_payable=total + penalty + gst,
            overdue_emis=[
                OverdueEMIItem(
                    emi_number=e.emi_number,
                    emi_amount=e.emi_amount,
                    due_date=e.due_date,
                    overdue_days=(today - e.due_date).days,
                    status=e.status,
                )
                for e in overdue_emis
            ],
        )

    # =====================================================
    # 💳 PAYMENT DETAILS
    # =====================================================
    payment_details = _get_lender_payment_details(
        db,
        application_id,
        payment_mode
    )

    # =====================================================
    # 🟢 REGULAR EMI
    # =====================================================
    if payment_option == PaymentOptionEnum.regular_emi:
        emi = _get_next_due_emi(db, application_id)
        emi.status = "PAID"

        txn = _save_payment(
            db,
            application_id,
            str(emi.emi_number),
            Decimal(str(emi.emi_amount)),
            payment_mode,
            payment_option,
            emi.due_date
        )

        txn.payment_date = emi.due_date
        db.commit()

        return PaymentResponse(
            transaction_id=txn.transaction_id,
            application_id=application_id,
            emi_number=emi.emi_number,
            emi_amount=emi.emi_amount,
            amount_paid=emi.emi_amount,
            payment_mode=payment_mode,
            payment_option=payment_option,
            date=emi.due_date,
            payment_details=payment_details,
        )

    # =====================================================
    # 🟡 PREPAY
    # =====================================================
    elif payment_option == PaymentOptionEnum.prepay:
        emi = _get_next_due_emi(db, application_id)
        emi.status = "PARTIAL"

        txn = _save_payment(
            db,
            application_id,
            str(emi.emi_number),
            Decimal(str(emi.emi_amount)),
            payment_mode,
            payment_option,
            emi.due_date
        )

        txn.payment_date = emi.due_date
        db.commit()

        return PaymentResponse(
            transaction_id=txn.transaction_id,
            application_id=application_id,
            emi_number=emi.emi_number,
            emi_amount=emi.emi_amount,
            amount_paid=emi.emi_amount,
            payment_mode=payment_mode,
            payment_option=payment_option,
            date=emi.due_date,
            payment_details=payment_details,
        )

    # =====================================================
    # 🔵 FORECLOSURE
    # =====================================================
    elif payment_option == PaymentOptionEnum.foreclosure:
        pending = _get_all_due_emis(db, application_id)

        total = Decimal(str(sum(e.emi_amount for e in pending)))
        emi_nums = ",".join(str(e.emi_number) for e in pending)

        for e in pending:
            e.status = "PAID"

        txn = _save_payment(
            db,
            application_id,
            emi_nums,
            total,
            payment_mode,
            payment_option,
            pending[-1].due_date
        )

        txn.payment_date = pending[-1].due_date
        db.commit()

        return PaymentResponse(
            transaction_id=txn.transaction_id,
            application_id=application_id,
            emi_number=None,
            emi_amount=total,
            amount_paid=total,
            payment_mode=payment_mode,
            payment_option=payment_option,
            date=pending[-1].due_date,
            payment_details=payment_details,
        )