import hmac
import hashlib
import os
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from schemas.Loan_application.razorpayx_webhook_schema import (
    RazorpayWebhookSchema
)

from core.session import get_db
from core.enums import (
    DisbursementStatusEnum,
    LoanApplicationStatus
)

from models.Loan_application.loan_application import (
    LoanApplication
)

from repositories.Loan_application.loan_disbursement_repo import (
    LoanDisbursementRepository
)

logger = logging.getLogger("razorpayx_webhook")
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)


# =====================================================
# 🔐 VERIFY SIGNATURE
# =====================================================
def verify_signature(
    request_body: bytes,
    signature: str
):

    webhook_secret = os.getenv(
        "RAZORPAYX_WEBHOOK_SECRET"
    )

    if not webhook_secret:

        logger.error(
            "Webhook secret missing"
        )

        raise HTTPException(
            status_code=500,
            detail="Webhook configuration error"
        )

    generated_signature = hmac.new(
        webhook_secret.encode(),
        msg=request_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        generated_signature,
        signature
    ):

        logger.error(
            "Invalid webhook signature"
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )


# =====================================================
# 🔥 RAZORPAYX WEBHOOK
# =====================================================
@router.post("/razorpayx")
async def razorpayx_payout_webhook(
    payload_data: RazorpayWebhookSchema,
    request: Request,
    db: Session = Depends(get_db)
):

    # =====================================================
    # REQUEST BODY
    # =====================================================
    body = await request.body()

    # =====================================================
    # SIGNATURE
    # =====================================================
    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    # =====================================================
    # MOCK MODE
    # =====================================================
    if os.getenv(
        "USE_MOCK_PAYOUT",
        "true"
    ).lower() == "true":

        logger.info(
            "[MOCK MODE] Signature verification skipped"
        )

    else:

        if not signature:

            raise HTTPException(
                status_code=400,
                detail="Missing signature"
            )

        verify_signature(
            body,
            signature
        )

    # =====================================================
    # PAYLOAD
    # =====================================================
    data = payload_data.dict()

    event = data.get("event")

    logger.info(
        f"[WEBHOOK EVENT] {event}"
    )

    allowed_events = [
        "payout.processed",
        "payout.failed",
        "payout.reversed",
        "payout.processing",
        "payout.queued"
    ]

    if event not in allowed_events:

        return {
            "status": "ignored"
        }

    # =====================================================
    # PAYOUT ENTITY
    # =====================================================
    payout = (
        data.get("payload", {})
        .get("payout", {})
        .get("entity", {})
    )

    reference_id = payout.get(
        "reference_id"
    )

    status = payout.get(
        "status"
    )

    logger.info(
        f"[PAYOUT STATUS] "
        f"reference={reference_id}, "
        f"status={status}"
    )

    if not reference_id:

        return {
            "status": "missing_reference"
        }

    try:

        # =====================================================
        # FETCH DISBURSEMENT
        # =====================================================
        disbursement = (
            LoanDisbursementRepository.get_by_reference(
                db=db,
                reference_id=reference_id
            )
        )

        if not disbursement:

            logger.warning(
                f"Disbursement not found: "
                f"{reference_id}"
            )

            return {
                "status": "not_found"
            }

        # =====================================================
        # FETCH APPLICATION
        # =====================================================
        application = (
            db.query(LoanApplication)
            .filter(
                LoanApplication.id
                == disbursement.application_id
            )
            .first()
        )

        if not application:

            logger.error(
                f"Loan application not found: "
                f"{disbursement.application_id}"
            )

            return {
                "status": "application_not_found"
            }

        # =====================================================
        # IDEMPOTENCY
        # =====================================================
        if (
            disbursement.payment_status
            == DisbursementStatusEnum.SUCCESS
            and status == "processed"
        ):

            return {
                "status": "already_processed"
            }

        # =====================================================
        # 🟢 SUCCESS
        # =====================================================
        if status == "processed":

            disbursement.payment_status = (
                DisbursementStatusEnum.SUCCESS
            )

            disbursement.completed_at = (
                datetime.utcnow()
            )

            db.query(LoanApplication).filter(
                LoanApplication.id
                == disbursement.application_id
            ).update(
                {
                    "application_status":
                        LoanApplicationStatus.ACTIVE,

                    "payout_status":
                        DisbursementStatusEnum.SUCCESS,

                    "current_step":
                        "ACTIVE",

                    "disbursed_at":
                        datetime.utcnow(),

                    "updated_at":
                        datetime.utcnow()
                },
                synchronize_session=False
            )

        # =====================================================
        # 🔴 FAILED
        # =====================================================
        elif status in [
            "failed",
            "reversed"
        ]:

            disbursement.payment_status = (
                DisbursementStatusEnum.FAILED
            )

            db.query(LoanApplication).filter(
                LoanApplication.id
                == disbursement.application_id
            ).update(
                {
                    "payout_status":
                        DisbursementStatusEnum.FAILED,

                    "current_step":
                        "DISBURSEMENT_FAILED",

                    "updated_at":
                        datetime.utcnow()
                },
                synchronize_session=False
            )

        # =====================================================
        # 🟡 PROCESSING
        # =====================================================
        elif status in [
            "processing",
            "queued"
        ]:

            disbursement.payment_status = (
                DisbursementStatusEnum.PROCESSING
            )

            db.query(LoanApplication).filter(
                LoanApplication.id
                == disbursement.application_id
            ).update(
                {
                    "application_status":
                        LoanApplicationStatus.DISBURSEMENT_INITIATED,

                    "payout_status":
                        DisbursementStatusEnum.PROCESSING,

                    "current_step":
                        "DISBURSEMENT_PROCESSING",

                    "updated_at":
                        datetime.utcnow()
                },
                synchronize_session=False
            )

        else:

            return {
                "status": "ignored_status"
            }

        # =====================================================
        # UPDATE TRANSACTIONS
        # =====================================================
        if hasattr(
            disbursement,
            "transactions"
        ):

            for txn in disbursement.transactions:

                txn.status = (
                    disbursement.payment_status.value
                )

                db.add(txn)

        # =====================================================
        # SAVE
        # =====================================================
        db.add(disbursement)

        db.commit()

        logger.info(
            f"[WEBHOOK UPDATED] "
            f"application={application.id}, "
            f"status={status}"
        )

    except Exception as e:

        db.rollback()

        logger.error(
            f"Webhook processing failed: "
            f"{str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed"
        )

    # =====================================================
    # RESPONSE
    # =====================================================
    return {
        "status": "updated",
        "reference_id": reference_id,
        "payout_status": status
    }