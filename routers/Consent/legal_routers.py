from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from core.database import get_db
from consent.pdf_utils import generate_pdf
from models.Consent.consent_master import ConsentMaster
from core.dependencies import require_roles
router = APIRouter(prefix="/legal", tags=["Legal Docs"])
 
def get_doc_text(db: Session, doc_type: str):
    doc = db.query(ConsentMaster).filter(
        ConsentMaster.type == doc_type,
        ConsentMaster.active == True
    ).order_by(ConsentMaster.version.desc()).first()
 
    if not doc:
        return {"message": f"{doc_type} not found"}
 
    return {
        "type": doc.type,
        "version": doc.version,
        "content": doc.content
    }
 
@router.get("/terms")
def get_terms_and_conditions(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))  
):
    return get_doc_text(db, "Terms & Conditions")
 
 
@router.get("/privacy-policy")
def get_privacy_policy(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    return get_doc_text(db, "Privacy Policy")
 
 
@router.get("/data-consent")
def get_data_consent(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    return get_doc_text(db, "Data Consent")
 
 
@router.get("/credit-bureau")
def get_credit_bureau(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    return get_doc_text(db, "Credit Bureau Consent")
 
 
@router.get("/terms/pdf")
def download_terms_and_conditions(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    doc = get_doc_text(db, "Terms & Conditions")
    file_path = generate_pdf("terms", doc["content"])
    return FileResponse(file_path, filename="terms_conditions.pdf")
 
 
@router.get("/privacy-policy/pdf")
def download_privacy_policy(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    doc = get_doc_text(db, "Privacy Policy")
    file_path = generate_pdf("privacy", doc["content"])
    return FileResponse(file_path, filename="privacy_policy.pdf")
 
 
@router.get("/data-consent/pdf")
def download_data_consent(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    doc = get_doc_text(db, "Data Consent")
    file_path = generate_pdf("data_consent", doc["content"])
    return FileResponse(file_path, filename="data_consent.pdf")
 
 
@router.get("/credit-bureau/pdf")
def download_credit_bureau_consent(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("USER"))
):
    doc = get_doc_text(db, "Credit Bureau Consent")
    file_path = generate_pdf("credit_bureau", doc["content"])
    return FileResponse(file_path, filename="credit_bureau_consent.pdf")
