from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from core.database import get_db
from core.dependencies import require_roles
from core.logger import logger

from models.Auth.user import User

from services.Esign.agreement_service import AgreementService
from services.Esign.pdf_generator import PDFGenerator

from schemas.Esign.agreement_schema import AgreementResponse


router = APIRouter(
    prefix="/loan/agreement",
    tags=["Agreement"]
)


# =====================================================
# DEPENDENCY
# =====================================================
def get_agreement_service() -> AgreementService:
    return AgreementService(pdf=PDFGenerator())


# =====================================================
# GENERATE / FETCH AGREEMENT
# =====================================================
@router.post("", response_model=AgreementResponse, operation_id="generate_agreement")
def generate_agreement(
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        logger.info(f"[AGREEMENT GENERATE] user={current_user.id}")

        result = service.fetch_agreement_for_user(
            user_id=current_user.id,
            db=db
        )

        if not result:
            raise HTTPException(404, "Agreement not found")

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[AGREEMENT ERROR] user={current_user.id}, error={str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Agreement generation failed"
        )


# =====================================================
# DOWNLOAD AGREEMENT (SAFE + SMART)
# =====================================================
@router.get("/download", operation_id="download_agreement")
def download_agreement(
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("USER"))
):
    try:
        logger.info(f"[AGREEMENT DOWNLOAD] user={current_user.id}")

        agreement = service.get_existing_agreement(
            user_id=current_user.id,
            db=db
        )

        if not agreement:
            raise HTTPException(404, "Agreement not generated yet")

        # -------------------------------------------------
        # 🔐 SAFE FIELD ACCESS (handles ORM or dict)
        # -------------------------------------------------
        user_id = getattr(agreement, "user_id", None)
        app_id = getattr(agreement, "application_id", None)
        status = getattr(agreement, "esign_status", None)
        signed_path = getattr(agreement, "signed_pdf_path", None)
        draft_path = getattr(agreement, "agreement_pdf_path", None)

        # -------------------------------------------------
        # 🔐 Ownership check
        # -------------------------------------------------
        if user_id != current_user.id:
            raise HTTPException(403, "Unauthorized access")

        # -------------------------------------------------
        # 📄 SMART FILE SELECTION
        # -------------------------------------------------
        file_path = signed_path if status == "SIGNED" and signed_path else draft_path

        if not file_path:
            raise HTTPException(404, "Agreement file not found")

        # -------------------------------------------------
        # 🔐 SECURE PATH VALIDATION
        # -------------------------------------------------
        base_dir = os.path.abspath("storage")
        abs_path = os.path.abspath(file_path)

        if not abs_path.startswith(base_dir):
            logger.warning(f"[SECURITY ALERT] path traversal attempt user={current_user.id}")
            raise HTTPException(403, "Invalid file path")

        if not os.path.exists(abs_path):
            raise HTTPException(404, "File missing on server")

        logger.info(f"[FILE SERVED] user={current_user.id}, file={abs_path}")

        return FileResponse(
            path=abs_path,
            media_type="application/pdf",
            filename=f"agreement_{app_id}.pdf"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[DOWNLOAD ERROR] user={current_user.id}, error={str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Failed to download agreement"
        )


# =====================================================
# VERIFY HASH (ADMIN ONLY)
# =====================================================
@router.post("/verify-hash", operation_id="verify_agreement_hash")
def verify_hash(
    file_hash: str,
    db: Session = Depends(get_db),
    service: AgreementService = Depends(get_agreement_service),
    current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN"))
):
    try:
        logger.info(f"[HASH VERIFY] admin={current_user.id}, hash={file_hash}")

        result = service.verify_hash(
            file_hash=file_hash,
            db=db
        )

        if not result:
            raise HTTPException(404, "Hash not found")

        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"[HASH VERIFY ERROR] admin={current_user.id}, error={str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Hash verification failed"
        )