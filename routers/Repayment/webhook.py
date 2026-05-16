from fastapi import (
    APIRouter,
    Request,
    Header,
    Depends
)

from sqlalchemy.orm import Session

import logging

from core.database import get_db

from services.Repayment.manual_payment import (
    process_webhook_event
)

from schemas.Repayment.webhook_schema import (
    OnlineWebhookSchema
)


# =====================================================
# LOGGER
# =====================================================
logger = logging.getLogger(
    "razorpay_payment_webhook"
)

logging.basicConfig(
    level=logging.INFO
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(
    prefix="/Repayment/webhook",
    tags=["RepaymentWebhook"]
)


# =====================================================
# 🔥 RAZORPAY PAYMENT WEBHOOK
# =====================================================
@router.post(
    "/razorpay",
    operation_id="razorpay_payment_webhook"
)
async def razorpay_payment_webhook(

    # =====================================================
    # SWAGGER BODY
    # =====================================================
    payload: OnlineWebhookSchema,

    request: Request,

    # =====================================================
    # OPTIONAL IN MOCK MODE
    # =====================================================
    x_razorpay_signature: str = Header(
        default=None
    ),

    db: Session = Depends(get_db)
):
    """
    =====================================================
    SUPPORTED METHODS
    =====================================================

    - UPI
    - CARD
    - NETBANKING
    - BANK_TRANSFER

    =====================================================
    SUPPORTED EVENTS
    =====================================================

    - payment.captured
    - payment.failed

    =====================================================
    SUPPORTED FLOWS
    =====================================================

    - REGULAR EMI
    - PREPAY
    - FORECLOSURE

    =====================================================
    MOCK MODE
    =====================================================

    Signature validation skipped for local testing.
    """

    # =====================================================
    # PYDANTIC → DICT
    # =====================================================
    payload = payload.model_dump()

    # =====================================================
    # RAW BODY
    # =====================================================
    body = await request.body()

    # =====================================================
    # MOCK MODE
    # =====================================================
    logger.info(
        "🧪 MOCK MODE ENABLED | "
        "Signature verification skipped"
    )

    # =====================================================
    # EVENT TYPE
    # =====================================================
    event = payload.get("event")

    # =====================================================
    # ALLOWED EVENTS
    # =====================================================
    allowed_events = [
        "payment.captured",
        "payment.failed"
    ]

    if event not in allowed_events:

        logger.info(
            f"⚠️ Ignored event: {event}"
        )

        return {
            "status": "ignored",
            "event": event
        }

    logger.info(
        f"📩 Razorpay Event Received: "
        f"{event}"
    )

    # =====================================================
    # PAYMENT ENTITY
    # =====================================================
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

    amount = entity.get("amount")

    method = entity.get("method")

    payment_status = entity.get("status")

    # =====================================================
    # REMOVE SWAGGER DEFAULT VALUE
    # =====================================================
    if order_id == "string":

        order_id = None

        entity["order_id"] = None

    if payment_id == "string":

        payment_id = None

        entity["id"] = None

    # =====================================================
    # LOG PAYMENT
    # =====================================================
    logger.info(

        f"💳 PAYMENT DETAILS | "

        f"payment_id={payment_id}, "

        f"order_id={order_id}, "

        f"method={method}, "

        f"amount={amount}, "

        f"status={payment_status}"
    )

    # =====================================================
    # SUPPORTED METHODS
    # =====================================================
    supported_methods = [
        "upi",
        "card",
        "netbanking",
        "bank_transfer"
    ]

    if (
        method
        and method.lower()
        not in supported_methods
    ):

        logger.warning(

            f"⚠️ Unsupported payment method: "
            f"{method}"
        )

        return {

            "status": "ignored",

            "message":
                f"Unsupported method {method}"
        }

    # =====================================================
    # BANK TRANSFER VALIDATION
    # =====================================================
    if (
        method
        and method.lower()
        == "bank_transfer"
        and not payment_id
    ):

        return {

            "status": "error",

            "message":
                "transaction_id required "
                "for BANK_TRANSFER"
        }

    # =====================================================
    # ONLINE PAYMENT VALIDATION
    # =====================================================
    if (
        method
        and method.lower() in [
            "upi",
            "card",
            "netbanking"
        ]
        and not order_id
    ):

        return {

            "status": "error",

            "message":
                "order_id required "
                "for online payments"
        }

    # =====================================================
    # PROCESS WEBHOOK
    # =====================================================
    try:

        result = process_webhook_event(
            db,
            payload
        )

        logger.info(
            f"✅ Processed {event}: "
            f"{result}"
        )

        return {

            "status": "ok",

            "event": event,

            "payment_id": payment_id,

            "order_id": order_id,

            "method": method,

            "data": result
        }

    except Exception as e:

        logger.error(
            f"❌ Error processing webhook: "
            f"{str(e)}"
        )

        # =====================================================
        # IMPORTANT:
        # RETURN 200 TO STOP RAZORPAY RETRIES
        # =====================================================
        return {

            "status": "error",

            "message": str(e)
        }