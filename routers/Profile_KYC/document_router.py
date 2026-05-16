from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import require_roles
from models.Auth.user import User
from schemas.Profile_KYC.document_schema import (
    BulkDocumentUploadResponse,
    SingleDocumentResult,
    AllDocumentsResponse,
    DocumentListItem,
    IncomeTypeEnum,
)
from services.Profile_KYC.document_upload_service import DocumentUploadService

router = APIRouter(prefix="/kyc/documents", tags=["Document Upload"])


# =====================================================
# POST /upload
# Upload → Cloudinary → OCR auto-verify → Save status
# =====================================================
@router.post("/upload", response_model=BulkDocumentUploadResponse)
async def upload_documents(
    pan_card:      Optional[UploadFile] = File(None, description="PAN Card — JPG/PNG, max 2 MB"),
    aadhaar_front: Optional[UploadFile] = File(None, description="Aadhaar Front — JPG/PNG, max 2 MB"),
    aadhaar_back:  Optional[UploadFile] = File(None, description="Aadhaar Back — JPG/PNG, max 2 MB"),
    income_proof:  Optional[UploadFile] = File(None, description="Salary Slip or Bank Statement — PDF, max 3 MB"),
    income_type:   Optional[IncomeTypeEnum] = Form(None, description="SALARY_SLIP or BANK_STATEMENT"),
    db:            Session              = Depends(get_db),
    current_user:  User                 = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    files_provided = [f for f in [pan_card, aadhaar_front, aadhaar_back, income_proof] if f and f.filename]
    if not files_provided:
        raise HTTPException(400, "No files provided. Please attach at least one document.")

    IMAGE_MAX = 2 * 1024 * 1024
    PDF_MAX   = 3 * 1024 * 1024

    file_bytes: dict[str, bytes] = {}

    for field_name, file, label, max_bytes in [
        ("pan_card",      pan_card,      "PAN Card",      IMAGE_MAX),
        ("aadhaar_front", aadhaar_front, "Aadhaar Front", IMAGE_MAX),
        ("aadhaar_back",  aadhaar_back,  "Aadhaar Back",  IMAGE_MAX),
        ("income_proof",  income_proof,  "Income Proof",  PDF_MAX),
    ]:
        if file and file.filename:
            content = await file.read()   # one async read; cursor at EOF after this
            if len(content) > max_bytes:
                max_mb    = max_bytes / (1024 * 1024)
                actual_mb = round(len(content) / (1024 * 1024), 2)
                raise HTTPException(400, {
                    "error":          "File too large",
                    "field":          label,
                    "file_size_mb":   actual_mb,
                    "max_allowed_mb": max_mb,
                    "message":        f"{label}: {actual_mb} MB exceeds the {max_mb} MB limit.",
                })
            file_bytes[field_name] = content

    try:
        result   = DocumentUploadService.bulk_upload_documents(
            db            = db,
            user_id       = profile.user_id,
            pan_card      = pan_card,
            aadhaar_front = aadhaar_front,
            aadhaar_back  = aadhaar_back,
            income_proof  = income_proof,
            income_type   = income_type.value if income_type else None,
            file_bytes    = file_bytes,
        )
        uploaded = [SingleDocumentResult(**doc) for doc in result["uploaded_documents"]]
        return BulkDocumentUploadResponse(
            user_id               = result["user_id"],
            email                 = result["email"],
            uploaded_documents    = uploaded,
            total_uploaded        = result["total_uploaded"],
            skipped_approved      = result["skipped_approved"],
            skipped_empty         = result["skipped_empty"],
            missing_documents     = result["missing_documents"],
            all_required_uploaded = result["all_required_uploaded"],
            document_status       = result["document_status"],
            kyc_status            = result["kyc_status"],
            message               = result["message"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, f"Document upload failed: {exc}")


# =====================================================
# GET /list
# =====================================================
@router.get("/list", response_model=AllDocumentsResponse)
def list_documents(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    try:
        result    = DocumentUploadService.list_documents(db=db, user_id=profile.user_id)
        documents = [DocumentListItem(**doc) for doc in result["documents"]]
        return AllDocumentsResponse(
            user_id            = result["user_id"],
            email              = result["email"],
            documents          = documents,
            total_documents    = result["total_documents"],
            required_documents = result["required_documents"],
            missing_documents  = result["missing_documents"],
            all_approved       = result["all_approved"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Failed to retrieve documents")


# =====================================================
# DELETE /{document_id}
# Blocked if status == APPROVED.
# =====================================================
@router.delete("/{document_id}")
def delete_document(
    document_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(require_roles("USER")),
):
    profile = current_user.profile
    if not profile:
        raise HTTPException(404, "KYC profile not found")

    try:
        return DocumentUploadService.delete_document(
            db          = db,
            document_id = document_id,
            user_id     = profile.user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Failed to delete document")