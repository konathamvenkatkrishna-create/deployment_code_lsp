from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from core.logger import logger

from services.Tracking.nbfc_service import NBFCService
from schemas.Tracking.webhook_schema import (
    NBFCWebhookRequest,
    NBFCWebhookResponse
)

from utils.signature import verify_callback_signature


router = APIRouter(
    prefix="/webhook",
    tags=["NBFC Webhooks"]
)


@router.post(
    "/nbfc",
    response_model=NBFCWebhookResponse,
    operation_id="receive_nbfc_webhook"
)
async def receive_nbfc_webhook(
    request: Request,
    payload: NBFCWebhookRequest,
    db: Session = Depends(get_db),
    x_signature: str | None = Header(None, alias="X-Signature"),
):
    raw_body = await request.body()

    try:
        logger.info(
            f"[NBFC WEBHOOK RECEIVED] txn={payload.transaction_id}, app={payload.application_id}"
        )

        # ------------------------------------------------
        # 🔐 SIGNATURE VALIDATION
        # ------------------------------------------------
        if settings.ENV.upper() != "DEV":

            if not x_signature:
                logger.warning("[WEBHOOK ERROR] Missing signature")
                raise HTTPException(401, "Missing X-Signature header")

            if not verify_callback_signature(raw_body, x_signature):
                logger.warning(f"[WEBHOOK ERROR] Invalid signature txn={payload.transaction_id}")
                raise HTTPException(403, "Invalid signature")

        else:
            logger.warning("[DEV MODE] Skipping signature validation")

        # ------------------------------------------------
        # 🔁 IDEMPOTENCY CHECK (CRITICAL)
        # ------------------------------------------------
        if NBFCService.is_duplicate_event(db, payload.transaction_id):
            logger.info(f"[DUPLICATE WEBHOOK] txn={payload.transaction_id}")

            return {
                "success": True,
                "message": "Duplicate webhook ignored"
            }

        # ------------------------------------------------
        # ⚙️ PROCESS WEBHOOK
        # ------------------------------------------------
        result = NBFCService.process_webhook(
            db=db,
            data=payload.dict()
        )

        logger.info(
            f"[WEBHOOK SUCCESS] txn={payload.transaction_id}, app={payload.application_id}"
        )

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"[WEBHOOK FAILED] txn={payload.transaction_id}, error={str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )