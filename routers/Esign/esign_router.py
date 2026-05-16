from fastapi import APIRouter, Depends, Request, Header, Body, HTTPException
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from services.Esign.esign_service import EsignService

from schemas.Esign.esign_schema import VerifyRequest
from schemas.Esign.callback_schema import EsignCallbackRequest

from utils.signature import verify_callback_signature
from utils.response import success_response

from models.Esign.esign_session import EsignSession, EsignStatus


router = APIRouter(
    prefix="/loan/esign",
    tags=["E-Sign"]
)


# =====================================================
# DEPENDENCY
# =====================================================
def get_esign_service() -> EsignService:
    return EsignService()


# =====================================================
# INITIATE ESIGN
# =====================================================
@router.post("/initiate", operation_id="initiate_esign")
async def initiate_esign(
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),
    current_user=Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    try:
        logger.info(f"[ESIGN INIT] user_id={current_user.id}")

        result = await service.initiate_esign(
            db=db,
            user_id=current_user.id
        )

        return success_response(result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[ESIGN INIT ERROR] user={current_user.id}, error={str(e)}")
        raise HTTPException(500, "Failed to initiate eSign")


# =====================================================
# VERIFY OTP (🔥 FIXED)
# =====================================================
@router.post("/verify", operation_id="verify_esign")
async def verify_esign(
    request_data: VerifyRequest,
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),
    current_user=Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN"))
):
    try:
        logger.info(f"[ESIGN VERIFY] txn={request_data.transaction_id}")

        session = db.query(EsignSession).filter(
            EsignSession.transaction_id == request_data.transaction_id
        ).with_for_update().first()

        if not session or session.user_id != current_user.id:
            raise HTTPException(403, "Unauthorized transaction access")

        if session.status == EsignStatus.SIGNED:
            raise HTTPException(400, "eSign already completed")

        # ❌ REMOVED expires_at check (not in DB)

        result = await service.verify_esign(
            data=request_data,
            db=db
        )

        return success_response(result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[ESIGN VERIFY ERROR] txn={request_data.transaction_id}, error={str(e)}")
        raise HTTPException(500, "OTP verification failed")


# =====================================================
# CALLBACK
# =====================================================
@router.post("/callback", operation_id="esign_callback")
async def esign_callback(
    request: Request,
    callback_body: EsignCallbackRequest = Body(...),
    db: Session = Depends(get_db),
    service: EsignService = Depends(get_esign_service),
    x_signature: str | None = Header(None, alias="X-Signature"),
):
    try:
        logger.info(f"[ESIGN CALLBACK] txn={callback_body.transaction_id}")

        raw_body = await request.body()

        if settings.ENV.upper() == "DEV" and getattr(settings, "ALLOW_INSECURE_CALLBACK", False):
            logger.warning("[CALLBACK DEV MODE] skipping signature validation")
        else:
            if not x_signature:
                raise HTTPException(401, "Missing X-Signature header")

            if not verify_callback_signature(raw_body, x_signature):
                logger.warning(f"[INVALID SIGNATURE] txn={callback_body.transaction_id}")
                raise HTTPException(403, "Invalid callback signature")

        session = db.query(EsignSession).filter(
            EsignSession.transaction_id == callback_body.transaction_id
        ).with_for_update().first()

        if not session:
            raise HTTPException(404, "Session not found")

        if session.status == EsignStatus.SIGNED:
            logger.info(f"[DUPLICATE CALLBACK IGNORED] txn={callback_body.transaction_id}")
            return success_response({"message": "Already processed"})

        result = await service.handle_callback(callback_body, db)

        logger.info(f"[CALLBACK SUCCESS] txn={callback_body.transaction_id}")

        return success_response(result)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[CALLBACK ERROR] txn={callback_body.transaction_id}, error={str(e)}")
        raise HTTPException(500, "Callback processing failed")