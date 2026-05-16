from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

from models.Repayment.emi_scheduled import (
    EMISchedule
)

from models.Repayment.payments import (
    Payment_Transaction
)

from models.Repayment.foreclosure import (
    ForeclosureRequest
)

from models.Loan_application.loan_application import (
    LoanApplication
)

from services.payment.razorpay_service import (
    RazorpayService
)


# =====================================================
# GET ACTIVE LOAN
# =====================================================
def _get_active_loan(
    db: Session,
    user_id: int
):

    loan = db.query(
        LoanApplication
    ).filter(

        LoanApplication.user_profile_id
        == user_id,

        LoanApplication.application_status
        == "ACTIVE"

    ).first()

    if not loan:

        raise HTTPException(
            status_code=404,
            detail="No ACTIVE loan found"
        )

    return loan


# =====================================================
# FORECLOSURE SUMMARY
# =====================================================
def create_foreclosure_request(
    db: Session,
    user_id: int
):

    loan = _get_active_loan(
        db,
        user_id
    )

    # =================================================
    # FETCH UNPAID EMIS
    # =================================================
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

    ).all()

    if not emis:

        raise HTTPException(
            status_code=400,
            detail="Nothing to foreclose"
        )

    # =================================================
    # TOTAL LOAN AMOUNT
    # =================================================
    total_loan_amount = float(
        loan.total_repayment or 0
    )

    # =================================================
    # SUCCESSFUL PAYMENTS
    # =================================================
    successful_payments = db.query(
        Payment_Transaction
    ).filter(

        Payment_Transaction.application_id
        == loan.id,

        Payment_Transaction.status
        == "SUCCESS"

    ).all()

    total_paid_amount = sum(
        float(p.amount_paid or 0)
        for p in successful_payments
    )

    # =================================================
    # OUTSTANDING
    # =================================================
    outstanding = max(
        total_loan_amount
        - total_paid_amount,
        0
    )

    if outstanding <= 0:

        raise HTTPException(
            status_code=400,
            detail="Loan already fully paid"
        )

    # =================================================
    # FORECLOSURE CHARGE
    # =================================================
    foreclosure_charge = round(
        outstanding * 0.02,
        2
    )

    # =================================================
    # GST
    # =================================================
    gst = round(
        foreclosure_charge * 0.18,
        2
    )

    # =================================================
    # TOTAL PAYABLE
    # =================================================
    total_amount = round(
        outstanding
        + foreclosure_charge
        + gst,
        2
    )

    # =================================================
    # DELETE OLD PENDING REQUEST
    # =================================================
    existing = db.query(
        ForeclosureRequest
    ).filter(

        ForeclosureRequest.application_id
        == loan.id,

        ForeclosureRequest.status
        == "PENDING"

    ).first()

    if existing:

        db.delete(existing)

        db.commit()

    # =================================================
    # CREATE NEW REQUEST
    # =================================================
    foreclosure = ForeclosureRequest(

        application_id=
            loan.id,

        outstanding=
            Decimal(str(outstanding)),

        charge=
            Decimal(str(foreclosure_charge)),

        gst=
            Decimal(str(gst)),

        total_amount=
            Decimal(str(total_amount)),

        status=
            "PENDING"
    )

    db.add(foreclosure)

    db.commit()

    db.refresh(foreclosure)

    # =================================================
    # RESPONSE
    # =================================================
    return {

        "message":
            "Foreclosure summary generated",

        "foreclosure_id":
            foreclosure.id,

        "application_id":
            loan.id,

        "total_loan_amount":
            round(total_loan_amount, 2),

        "total_paid_amount":
            round(total_paid_amount, 2),

        "remaining_pending_amount":
            round(outstanding, 2),

        "foreclosure_charges":
            round(foreclosure_charge, 2),

        "gst_on_charges":
            round(gst, 2),

        "final_payable_amount":
            round(total_amount, 2)
    }


# =====================================================
# INITIATE FORECLOSURE PAYMENT
# =====================================================
def initiate_foreclosure_payment(
    db: Session,
    foreclosure_id: int
):

    foreclosure = db.query(
        ForeclosureRequest
    ).filter(
        ForeclosureRequest.id
        == foreclosure_id
    ).first()

    if not foreclosure:

        raise HTTPException(
            status_code=404,
            detail="Foreclosure request not found"
        )

    if foreclosure.status != "PENDING":

        raise HTTPException(
            status_code=400,
            detail="Invalid foreclosure status"
        )

    # =================================================
    # DUPLICATE CHECK
    # =================================================
    existing_txn = db.query(
        Payment_Transaction
    ).filter(

        Payment_Transaction.application_id
        == foreclosure.application_id,

        Payment_Transaction.payment_option
        == "FORECLOSURE",

        Payment_Transaction.status.in_([
            "INITIATED",
            "RETRY",
            "SUCCESS"
        ])

    ).first()

    if existing_txn:

        if existing_txn.status in [
            "INITIATED",
            "RETRY"
        ]:

            return {

                "message":
                    "Foreclosure payment already initiated",

                "transaction_id":
                    existing_txn.transaction_id,

                "order_id":
                    existing_txn.order_id,

                "status":
                    existing_txn.status
            }

        raise HTTPException(
            status_code=400,
            detail="Foreclosure already completed"
        )

    rzp = RazorpayService()

    # =================================================
    # CREATE ORDER
    # =================================================
    order = rzp.create_order(

        float(
            foreclosure.total_amount
        ),

        receipt=
            f"foreclosure_{foreclosure.id}"
    )

    foreclosure.order_id = order["id"]

    txn = Payment_Transaction(

        application_id=
            foreclosure.application_id,

        emi_number=
            "FORECLOSURE",

        amount_paid=
            Decimal("0"),

        payment_mode=
            "ONLINE",

        payment_option=
            "FORECLOSURE",

        order_id=
            order["id"],

        status=
            "INITIATED",

        retry_count=
            0,

        created_at=
            datetime.utcnow()
    )

    db.add(txn)

    db.commit()

    return {

        "message":
            "Foreclosure payment initiated",

        "order_id":
            order["id"],

        "amount":
            order["amount"],

        "currency":
            order["currency"],

        "key":
            "RAZORPAY_KEY_ID"
    }


# =====================================================
# FORECLOSURE WEBHOOK
# =====================================================
def process_foreclosure_webhook(
    db: Session,
    body: bytes,
    signature: str,
    payload: dict
):

    rzp = RazorpayService()

    try:

        rzp.verify_webhook(
            body,
            signature
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid webhook: {str(e)}"
        )

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

        # =================================================
        # FIND TRANSACTION
        # =================================================
        if order_id:

            txn = db.query(
                Payment_Transaction
            ).filter(

                Payment_Transaction.order_id
                == order_id,

                Payment_Transaction.payment_option
                == "FORECLOSURE"

            ).first()

        else:

            # MOCK PAYMENT SUPPORT
            txn = db.query(
                Payment_Transaction
            ).filter(

                Payment_Transaction.payment_option
                == "FORECLOSURE",

                Payment_Transaction.status.in_([
                    "INITIATED",
                    "RETRY"
                ])

            ).order_by(
                Payment_Transaction.payment_id.desc()
            ).first()

        if not txn:

            return {
                "message":
                    "Foreclosure transaction not found"
            }

        # =================================================
        # ALREADY SUCCESS
        # =================================================
        if txn.status == "SUCCESS":

            return {
                "message":
                    "Foreclosure already processed"
            }

        # =================================================
        # FIND FORECLOSURE REQUEST
        # =================================================
        foreclosure = db.query(
            ForeclosureRequest
        ).filter(

            ForeclosureRequest.application_id
            == txn.application_id

        ).order_by(
            ForeclosureRequest.id.desc()
        ).first()

        if not foreclosure:

            return {
                "message":
                    "Foreclosure request not found"
            }

        # =================================================
        # UPDATE TRANSACTION
        # =================================================
        txn.transaction_id = payment_id

        txn.amount_paid = Decimal(
            str(amount)
        )

        txn.status = "SUCCESS"

        db.add(txn)

        # =================================================
        # UPDATE FORECLOSURE
        # =================================================
        foreclosure.payment_id = str(
            payment_id
        )

        foreclosure.order_id = (
            str(order_id)
            if order_id else None
        )

        foreclosure.status = "SUCCESS"

        db.add(foreclosure)

        # =================================================
        # MARK ALL EMIS PAID
        # =================================================
        all_emis = db.query(
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

        now = datetime.utcnow()

        for emi in all_emis:

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

        # =================================================
        # CLOSE LOAN
        # =================================================
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

                loan.loan_status = "FORECLOSED"

            if hasattr(
                loan,
                "closed_date"
            ):

                loan.closed_date = now

            db.add(loan)

        db.flush()

        db.commit()

        db.refresh(txn)

        return {

            "message":
                "Foreclosure successful",

            "loan_status":
                "CLOSED",

            "payment_id":
                payment_id
        }

    # =================================================
    # PAYMENT FAILED
    # =================================================
    elif event == "payment.failed":

        if order_id:

            txn = db.query(
                Payment_Transaction
            ).filter(

                Payment_Transaction.order_id
                == order_id,

                Payment_Transaction.payment_option
                == "FORECLOSURE"

            ).first()

        else:

            txn = db.query(
                Payment_Transaction
            ).filter(

                Payment_Transaction.payment_option
                == "FORECLOSURE",

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

            foreclosure = db.query(
                ForeclosureRequest
            ).filter(
                ForeclosureRequest.application_id
                == txn.application_id
            ).order_by(
                ForeclosureRequest.id.desc()
            ).first()

            if foreclosure:

                foreclosure.status = "FAILED"

                db.add(foreclosure)

            db.flush()

            db.commit()

        return {

            "message":
                "Foreclosure payment failed"
        }

    # =================================================
    # IGNORE OTHER EVENTS
    # =================================================
    return {

        "message":
            "Event ignored"
    }