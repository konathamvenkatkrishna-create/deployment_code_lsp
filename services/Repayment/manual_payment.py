import uuid

from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime

from models.Repayment.emi_scheduled import EMISchedule

from models.Repayment.lender_payment_details import (
    LenderPaymentDetails
)

from models.Loan_application.loan_application import (
    LoanApplication
)

from models.Repayment.payments import (
    Payment_Transaction
)

from models.Repayment.prepayments import (
    PrepaymentRequest
)

from models.Repayment.foreclosure import (
    ForeclosureRequest
)


# =====================================================
# COMMON: FETCH ACTIVE LOAN + NEXT EMI
# =====================================================
def _get_active_loan_and_emi(
    db: Session,
    user_id: int
):

    loan = db.query(
        LoanApplication
    ).filter(

        LoanApplication.user_profile_id == user_id,

        LoanApplication.application_status == "ACTIVE"

    ).first()

    if not loan:

        raise HTTPException(
            status_code=404,
            detail="No ACTIVE loan found"
        )

    emi = db.query(
        EMISchedule
    ).filter(

        EMISchedule.application_id == loan.id,

        EMISchedule.status.in_([
            "DUE",
            "PENDING",
            "UNPAID",
            "OVERDUE"
        ])

    ).order_by(
        EMISchedule.emi_number
    ).first()

    return loan, emi


# =====================================================
# STEP 1: PAYMENT SUMMARY
# =====================================================
def get_payment_summary(
    db: Session,
    user_id: int,
    payment_option: str = "REGULAR"
):

    payment_option = payment_option.upper()

    loan, emi = _get_active_loan_and_emi(
        db,
        user_id
    )

    # =================================================
    # REGULAR EMI
    # =================================================
    if payment_option == "REGULAR":

        if not emi:

            raise HTTPException(
                status_code=404,
                detail="No pending EMI found"
            )

        return {

            "payment_type": "REGULAR",

            "total_due": float(
                emi.emi_amount
            ),

            "remaining_emis": 1,

            "emis": [
                {
                    "emi_number":
                        emi.emi_number,

                    "amount":
                        float(emi.emi_amount),

                    "due_date":
                        emi.due_date,

                    "status":
                        emi.status
                }
            ]
        }

    # =================================================
    # ALL PENDING EMIs
    # =================================================
    emis = db.query(
        EMISchedule
    ).filter(

        EMISchedule.application_id == loan.id,

        EMISchedule.status.in_([
            "DUE",
            "PENDING",
            "UNPAID",
            "OVERDUE"
        ])

    ).order_by(
        EMISchedule.emi_number
    ).all()

    if not emis:

        raise HTTPException(
            status_code=404,
            detail="No pending EMIs found"
        )

    outstanding = round(
        sum(
            float(e.emi_amount)
            for e in emis
        ),
        2
    )

    # =================================================
    # PREPAY
    # =================================================
    if payment_option == "PREPAY":

        return {

            "payment_type": "PREPAY",

            "total_due": outstanding,

            "remaining_emis": len(emis),

            "emis": [
                {
                    "emi_number":
                        e.emi_number,

                    "amount":
                        float(e.emi_amount),

                    "due_date":
                        e.due_date,

                    "status":
                        e.status
                }
                for e in emis
            ]
        }

    # =================================================
    # FORECLOSURE
    # =================================================
    if payment_option == "FORECLOSURE":

        foreclosure_charge = round(
            outstanding * 0.02,
            2
        )

        gst = round(
            foreclosure_charge * 0.18,
            2
        )

        total_due = round(
            outstanding
            + foreclosure_charge
            + gst,
            2
        )

        return {

            "payment_type": "FORECLOSURE",

            "outstanding": outstanding,

            "foreclosure_charge":
                foreclosure_charge,

            "gst":
                gst,

            "total_due":
                total_due,

            "remaining_emis":
                len(emis),

            "emis": [
                {
                    "emi_number":
                        e.emi_number,

                    "amount":
                        float(e.emi_amount),

                    "due_date":
                        e.due_date,

                    "status":
                        e.status
                }
                for e in emis
            ]
        }

    raise HTTPException(
        status_code=400,
        detail="Invalid payment option"
    )


# =====================================================
# STEP 2: INITIATE PAYMENT
# =====================================================
def initiate_payment(
    db: Session,
    user_id: int,
    payment_mode: str,
    payment_option: str = "REGULAR",
    custom_amount: float = None
):

    payment_option = payment_option.upper()

    loan, emi = _get_active_loan_and_emi(
        db,
        user_id
    )

    # =================================================
    # PREPAY / FORECLOSURE
    # =================================================
    if payment_option in [
        "PREPAY",
        "FORECLOSURE"
    ]:

        emis = db.query(
            EMISchedule
        ).filter(

            EMISchedule.application_id
            == loan.id,

            EMISchedule.status.in_([
                "DUE",
                "PENDING",
                "UNPAID",
                "OVERDUE"
            ])

        ).order_by(
            EMISchedule.emi_number
        ).all()

        if not emis:

            raise HTTPException(
                status_code=400,
                detail="No pending EMIs found"
            )

        outstanding = round(
            sum(
                float(e.emi_amount)
                for e in emis
            ),
            2
        )

        # =============================================
        # PREPAY
        # =============================================
        if payment_option == "PREPAY":

            amount = outstanding

            emi_number = "PREPAY"

            existing_prepay = db.query(
                PrepaymentRequest
            ).filter(

                PrepaymentRequest.application_id
                == loan.id,

                PrepaymentRequest.status
                != "PAID"

            ).first()

            if not existing_prepay:

                prepay_request = PrepaymentRequest(

                    application_id=loan.id,

                    emi_numbers="ALL",

                    amount=Decimal(str(amount)),

                    charge=Decimal("0"),

                    gst=Decimal("0"),

                    status="PENDING"
                )

                db.add(prepay_request)

                db.flush()

        # =============================================
        # FORECLOSURE
        # =============================================
        else:

            foreclosure_charge = round(
                outstanding * 0.02,
                2
            )

            gst = round(
                foreclosure_charge * 0.18,
                2
            )

            amount = round(
                outstanding
                + foreclosure_charge
                + gst,
                2
            )

            emi_number = "FORECLOSURE"

            existing_foreclosure = db.query(
                ForeclosureRequest
            ).filter(

                ForeclosureRequest.application_id
                == loan.id,

                ForeclosureRequest.status
                != "PAID"

            ).first()

            if not existing_foreclosure:

                foreclosure_request = ForeclosureRequest(

                    application_id=loan.id,

                    outstanding=Decimal(
                        str(outstanding)
                    ),

                    charge=Decimal(
                        str(foreclosure_charge)
                    ),

                    gst=Decimal(
                        str(gst)
                    ),

                    total_amount=Decimal(
                        str(amount)
                    ),

                    status="PENDING"
                )

                db.add(foreclosure_request)

                db.flush()

    # =================================================
    # REGULAR EMI
    # =================================================
    else:

        if not emi:

            raise HTTPException(
                status_code=404,
                detail="No pending EMI found"
            )

        amount = float(
            emi.emi_amount
        )

        emi_number = str(
            emi.emi_number
        )

    # =================================================
    # CUSTOM AMOUNT
    # =================================================
    if custom_amount:

        amount = float(custom_amount)

    # =================================================
    # DUPLICATE PAYMENT CHECK
    # =================================================
    existing = db.query(
        Payment_Transaction
    ).filter(

        Payment_Transaction.application_id
        == loan.id,

        Payment_Transaction.payment_option
        == payment_option,

        Payment_Transaction.payment_mode
        == payment_mode,

        Payment_Transaction.status.in_([
            "INITIATED",
            "RETRY"
        ])

    ).order_by(
        Payment_Transaction.payment_id.desc()
    ).first()

    if existing:

        return {

            "message":
                "Payment already initiated",

            "transaction_id":
                existing.transaction_id,

            "amount":
                float(existing.amount_paid),

            "status":
                existing.status
        }

    # =================================================
    # BANK TRANSFER
    # =================================================
    if payment_mode == "BANK_TRANSFER":

        payment = db.query(
            LenderPaymentDetails
        ).filter(

            LenderPaymentDetails.lender_id
            == loan.lender_id

        ).first()

        if not payment:

            raise HTTPException(
                status_code=404,
                detail="Bank details not configured"
            )

        transaction_ref = (
            f"{payment_option}_BANK_TXN_"
            f"{uuid.uuid4().hex[:12]}"
        )

        txn = Payment_Transaction(

            application_id=loan.id,

            emi_number=emi_number,

            amount_paid=Decimal(
                str(amount)
            ),

            payment_mode="BANK_TRANSFER",

            payment_option=payment_option,

            transaction_id=transaction_ref,

            status="INITIATED",

            retry_count=0,

            created_at=datetime.utcnow()
        )

        db.add(txn)

        db.commit()

        return {

            "mode": "BANK_TRANSFER",

            "payment_option":
                payment_option,

            "transaction_id":
                transaction_ref,

            "account_number":
                payment.account_number,

            "ifsc":
                payment.ifsc,

            "bank_name":
                payment.bank_name,

            "amount":
                amount
        }

    raise HTTPException(
        status_code=400,
        detail="Invalid payment mode"
    )


# =====================================================
# STEP 3: RETRY PAYMENT
# =====================================================
def retry_payment(
    db: Session,
    user_id: int
):

    loan, emi = _get_active_loan_and_emi(
        db,
        user_id
    )

    txn = db.query(
        Payment_Transaction
    ).filter(

        Payment_Transaction.application_id
        == loan.id,

        Payment_Transaction.status
        == "FAILED"

    ).order_by(
        Payment_Transaction.payment_id.desc()
    ).first()

    if not txn:

        raise HTTPException(
            status_code=404,
            detail="No failed payment found"
        )

    if txn.retry_count >= 3:

        raise HTTPException(
            status_code=400,
            detail="Retry limit exceeded"
        )

    txn.status = "RETRY"

    txn.retry_count += 1

    db.commit()

    return {

        "message":
            "Retry initiated",

        "transaction_id":
            txn.transaction_id,

        "amount":
            float(txn.amount_paid)
    }


# =====================================================
# WEBHOOK HANDLER
# =====================================================
def process_webhook_event(
    db: Session,
    payload: dict
):

    event = payload.get("event")

    entity = payload.get(
        "payload",
        {}
    ).get(
        "payment",
        {}
    ).get(
        "entity",
        {}
    )

    payment_id = entity.get("id")

    order_id = entity.get("order_id")

    amount = (
        entity.get("amount") or 0
    ) / 100

    # =================================================
    # PAYMENT SUCCESS
    # =================================================
    if event == "payment.captured":

        txn = None

        if order_id:

            txn = db.query(
                Payment_Transaction
            ).filter(
                Payment_Transaction.order_id
                == order_id
            ).first()

        if not txn:

            txn = db.query(
                Payment_Transaction
            ).filter(

                Payment_Transaction.payment_mode
                == "BANK_TRANSFER",

                Payment_Transaction.status.in_([
                    "INITIATED",
                    "RETRY"
                ])

            ).order_by(
                Payment_Transaction.payment_id.desc()
            ).first()

        if not txn:

            return {
                "status": "failed",
                "message":
                    "Payment transaction not found"
            }

        if txn.status == "SUCCESS":

            return {
                "status": "ok",
                "message":
                    "Payment already processed"
            }

        txn.transaction_id = payment_id

        txn.amount_paid = Decimal(
            str(amount)
        )

        txn.status = "SUCCESS"

        now = datetime.utcnow()

        # =============================================
        # PREPAY / FORECLOSURE
        # =============================================
        if txn.payment_option in [
            "PREPAY",
            "FORECLOSURE"
        ]:

            emis = db.query(
                EMISchedule
            ).filter(

                EMISchedule.application_id
                == txn.application_id,

                EMISchedule.status.in_([
                    "DUE",
                    "PENDING",
                    "UNPAID",
                    "OVERDUE"
                ])

            ).all()

            for emi in emis:

                emi.status = "PAID"

                if hasattr(
                    emi,
                    "payment_status"
                ):
                    emi.payment_status = "PAID"

                if hasattr(
                    emi,
                    "paid_date"
                ):
                    emi.paid_date = now

                db.add(emi)

            # =========================================
            # PREPAY TABLE
            # =========================================
            if txn.payment_option == "PREPAY":

                prepay = db.query(
                    PrepaymentRequest
                ).filter(

                    PrepaymentRequest.application_id
                    == txn.application_id

                ).order_by(
                    PrepaymentRequest.id.desc()
                ).first()

                if prepay:

                    prepay.status = "PAID"

                    db.add(prepay)

            # =========================================
            # FORECLOSURE TABLE
            # =========================================
            if txn.payment_option == "FORECLOSURE":

                foreclosure = db.query(
                    ForeclosureRequest
                ).filter(

                    ForeclosureRequest.application_id
                    == txn.application_id

                ).order_by(
                    ForeclosureRequest.id.desc()
                ).first()

                if foreclosure:

                    foreclosure.status = "SUCCESS"

                    foreclosure.payment_id = str(payment_id)

                    foreclosure.order_id = (str(order_id)
                    if order_id else None
                    )

                    db.add(foreclosure)
                    db.flush()

        # =============================================
        # REGULAR EMI
        # =============================================
        else:

            emi = db.query(
                EMISchedule
            ).filter(

                EMISchedule.application_id
                == txn.application_id,

                EMISchedule.emi_number
                == txn.emi_number

            ).first()

            if emi:

                emi.status = "PAID"

                db.add(emi)

        # =============================================
        # AUTO CLOSE LOAN
        # =============================================
        pending_emis = db.query(
            EMISchedule
        ).filter(

            EMISchedule.application_id
            == txn.application_id,

            EMISchedule.status.in_([
                "DUE",
                "PENDING",
                "UNPAID",
                "OVERDUE"
            ])

        ).count()

        if pending_emis == 0:

            loan = db.query(
                LoanApplication
            ).filter(
                LoanApplication.id
                == txn.application_id
            ).first()

            if loan:

                loan.application_status = "CLOSED"

                if hasattr(
                    loan,
                    "loan_status"
                ):

                    if txn.payment_option == "FORECLOSURE":

                        loan.loan_status = "FORECLOSED"

                    else:

                        loan.loan_status = "COMPLETED"

                if hasattr(
                    loan,
                    "closed_date"
                ):
                    loan.closed_date = now

                db.add(loan)

        db.add(txn)

        db.commit()

        return {

            "status": "ok",

            "payment_id":
                payment_id,

            "payment_option":
                txn.payment_option,

            "message":
                "Payment processed successfully"
        }

    # =================================================
    # PAYMENT FAILED
    # =================================================
    elif event == "payment.failed":

        txn = db.query(
            Payment_Transaction
        ).filter(

            Payment_Transaction.status.in_([
                "INITIATED",
                "RETRY"
            ])

        ).order_by(
            Payment_Transaction.payment_id.desc()
        ).first()

        if txn:

            txn.status = "FAILED"

            txn.retry_count += 1

            db.add(txn)

            db.commit()

        return {

            "status": "failed",

            "payment_id":
                payment_id,

            "message":
                "Payment failed"
        }

    return {
        "message": "Event ignored"
    }