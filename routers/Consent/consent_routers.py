from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_roles

from models.Auth.user import User
from models.Consent.audit_logs import AuditLog
from models.Consent.consent_master import ConsentMaster
from models.Consent.user_consent import UserConsent

from schemas.Consent.Consent_schemas import ConsentType


router = APIRouter(prefix="/consent", tags=["Consent"])


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "UNKNOWN"


# =====================================================
# USER - RECORD CONSENT
# =====================================================
@router.post("/record")
def record_consent(
    request: Request,
    consent_type: ConsentType = Form(...),
    accepted: bool = Form(...),
    scroll_completed: bool = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    user_id = current_user.id
    ip_address = get_client_ip(request)
    consent_type_value = consent_type.value

    if not scroll_completed:
        raise HTTPException(
            status_code=400,
            detail="Please scroll through the entire document before accepting.",
        )

    if not accepted:
        raise HTTPException(
            status_code=400,
            detail="Consent not provided. Please accept to continue.",
        )

    latest_doc = (
        db.query(ConsentMaster)
        .filter(
            ConsentMaster.type == consent_type_value,
            ConsentMaster.active == True,
        )
        .order_by(ConsentMaster.version.desc())
        .first()
    )

    if not latest_doc:
        raise HTTPException(
            status_code=404,
            detail="Consent document not found.",
        )

    existing = (
        db.query(UserConsent)
        .filter(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type_value,
            UserConsent.version == latest_doc.version,
            UserConsent.accepted == True,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Consent already accepted for the latest version.",
        )

    consent = UserConsent(
        user_id=user_id,
        consent_type=consent_type_value,
        version=latest_doc.version,
        accepted=True,
        scroll_completed=True,
        ip_address=ip_address,
        accepted_at=datetime.utcnow(),
    )

    audit = AuditLog(
        action="CONSENT_ACCEPTED",
        user_id=user_id,
        details=f"{consent_type_value} v{latest_doc.version} accepted from IP {ip_address}",
    )

    try:
        db.add(consent)
        db.add(audit)
        db.commit()
        db.refresh(consent)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record consent: {str(e)}",
        )

    return {
        "status": "success",
        "message": "Consent recorded successfully.",
        "data": {
            "user_id": user_id,
            "consent_type": consent_type_value,
            "version": latest_doc.version,
            "accepted": True,
            "scroll_completed": True,
            "ip_address": ip_address,
            "accepted_at": consent.accepted_at,
        },
    }


# =====================================================
# USER - CONSENT HISTORY
# =====================================================
@router.get("/history")
def get_consent_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER")),
):
    user_id = current_user.id

    user_exists = db.query(User).filter(User.id == user_id).first()

    if not user_exists:
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id. User does not exist.",
        )

    history = (
        db.query(UserConsent)
        .filter(UserConsent.user_id == user_id)
        .order_by(UserConsent.accepted_at.desc())
        .all()
    )

    if not history:
        return {
            "status": "success",
            "message": "No consent history found for this user.",
            "data": [],
        }

    return {
        "status": "success",
        "message": "Consent history fetched successfully.",
        "data": history,
    }