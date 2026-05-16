import io
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import cloudinary
import cloudinary.uploader
from core.config import settings

cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key    = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET,
    secure     = True,
)

from models.Profile_KYC.document_upload import DocumentUpload, DocumentType, DocumentStatus
from models.Profile_KYC.kyc_bank_verification import KYCBankVerification
from repositories.Profile_KYC.user_repository import UserRepository
from repositories.Profile_KYC.document_upload_repository import DocumentUploadRepository
from services.Profile_KYC.kyc_ocr_service import KYCService

IMAGE_MAX_BYTES  = 2 * 1024 * 1024   # 2 MB
INCOME_MAX_BYTES = 3 * 1024 * 1024   # 3 MB

ALLOWED_IMAGE_EXTENSIONS    = {".jpg", ".jpeg", ".png"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf"}

# OCR score thresholds
SCORE_APPROVE      = 85   # >= 85    → APPROVED
SCORE_UNDER_REVIEW = 60   # 60 – 84 → UNDER_REVIEW (admin checks)
                          # <  60   → REJECTED


class DocumentUploadService:

    REQUIRED_DOCS     = [DocumentType.AADHAAR_FRONT, DocumentType.AADHAAR_BACK, DocumentType.PAN_CARD]
    INCOME_PROOF_DOCS = [DocumentType.SALARY_SLIP, DocumentType.BANK_STATEMENT]

    CLOUDINARY_FOLDER_MAP = {
        DocumentType.PAN_CARD:       ("pan",     "document"),
        DocumentType.AADHAAR_FRONT:  ("aadhaar", "aadhaar_front"),
        DocumentType.AADHAAR_BACK:   ("aadhaar", "aadhaar_back"),
        DocumentType.BANK_STATEMENT: ("income",  "bank_statement"),
        DocumentType.SALARY_SLIP:    ("income",  "salary_slip"),
    }

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    @staticmethod
    def _get_bank_verification(db: Session, user_id: int):
        return (
            db.query(KYCBankVerification)
            .filter(
                KYCBankVerification.user_id == user_id,
                KYCBankVerification.status  == "VERIFIED",
            )
            .order_by(KYCBankVerification.verified_at.desc())
            .first()
        )

    @staticmethod
    def _check_missing(db: Session, user_id: int) -> list:
        all_docs       = DocumentUploadRepository.get_by_user_id(db, user_id)
        uploaded_types = [d.document_type for d in all_docs]
        missing        = []
        for req in DocumentUploadService.REQUIRED_DOCS:
            if req not in uploaded_types:
                missing.append(req.value)
        if not any(t in uploaded_types for t in DocumentUploadService.INCOME_PROOF_DOCS):
            missing.append("SALARY_SLIP or BANK_STATEMENT")
        return missing

    @staticmethod
    def _update_user_doc_status(db: Session, user, all_docs: list) -> None:
        approved_types = {d.document_type for d in all_docs if d.status == DocumentStatus.APPROVED}
        required_types = set(DocumentUploadService.REQUIRED_DOCS)
        income_types   = set(DocumentUploadService.INCOME_PROOF_DOCS)

        all_approved = (
            required_types.issubset(approved_types) and
            bool(approved_types & income_types)
        )
        if all_approved:
            user.document_status = "APPROVED"
            if (
                user.pan_status     == "VERIFIED" and
                user.aadhaar_status == "VERIFIED" and
                user.bank_status    == "VERIFIED"
            ):
                user.kyc_status = "COMPLETED"

        UserRepository.save(db)

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_file(file: UploadFile, doc_type: DocumentType, file_size: int) -> None:
        max_bytes = (
            INCOME_MAX_BYTES
            if doc_type in DocumentUploadService.INCOME_PROOF_DOCS
            else IMAGE_MAX_BYTES
        )
        if file_size > max_bytes:
            max_mb    = max_bytes / (1024 * 1024)
            actual_mb = round(file_size / (1024 * 1024), 2)
            raise HTTPException(400, {
                "error":          "File too large",
                "document_type":  doc_type.value,
                "file_size_mb":   actual_mb,
                "max_allowed_mb": max_mb,
                "message":        f"{doc_type.value}: {actual_mb} MB exceeds the {max_mb} MB limit.",
            })

        ext = os.path.splitext(file.filename)[1].lower()
        if doc_type in [DocumentType.PAN_CARD, DocumentType.AADHAAR_FRONT, DocumentType.AADHAAR_BACK]:
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise HTTPException(400, f"{doc_type.value} requires JPG or PNG. Got: {ext}.")
        elif doc_type in DocumentUploadService.INCOME_PROOF_DOCS:
            if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
                raise HTTPException(400, f"{doc_type.value} requires PDF. Got: {ext}.")

    # ── Cloudinary ────────────────────────────────────────────────────────────

    @staticmethod
    def _upload_to_cloudinary(user_id: int, doc_type: DocumentType, content: bytes) -> str:
        
        folder_name, file_name = DocumentUploadService.CLOUDINARY_FOLDER_MAP[doc_type]
        folder    = f"user_documents/{user_id}/{folder_name}"
        public_id = file_name   # just the filename, e.g. "document" or "aadhaar_front"

        try:
            result = cloudinary.uploader.upload(
                io.BytesIO(content),
                folder          = folder,
                public_id       = public_id,
                resource_type   = "auto",
                overwrite       = True,
                use_filename    = False,
                unique_filename = False,
            )
            return result["secure_url"]
        except Exception as e:
            raise HTTPException(500, f"Cloudinary upload failed: {str(e)}")

    @staticmethod
    def _delete_from_cloudinary(file_url: str) -> None:
        """Best-effort delete — never raises."""
        public_id = DocumentUploadService._extract_public_id(file_url)
        if not public_id:
            return
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
            cloudinary.uploader.destroy(public_id, resource_type="raw")
        except Exception:
            pass

    @staticmethod
    def _extract_public_id(url: str) -> Optional[str]:
        
        try:
            marker = "/upload/"
            idx    = url.find(marker)
            if idx == -1:
                return None
            after = url[idx + len(marker):]
            if after.startswith("v") and "/" in after:
                ver = after[1 : after.index("/")]
                if ver.isdigit():
                    after = after[after.index("/") + 1:]
            if "." in after.split("/")[-1]:
                after = after.rsplit(".", 1)[0]
            return after
        except Exception:
            return None

    # ── OCR ───────────────────────────────────────────────────────────────────

    @staticmethod
    def _bytes_to_tempfile(content: bytes, doc_type: DocumentType) -> str:
        
        suffix = ".pdf" if doc_type in DocumentUploadService.INCOME_PROOF_DOCS else ".png"
        tmp    = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(content)
            tmp.flush()
            return tmp.name
        finally:
            tmp.close()

    @staticmethod
    def _run_ocr(
        content:           bytes,
        doc_type:          DocumentType,
        user,
        bank_verification: Optional[object],
    ) -> tuple:
        
        ocr_result   = None
        ocr_verified = False
        raw_text     = ""
        tmp_path     = None

        try:
            tmp_path = DocumentUploadService._bytes_to_tempfile(content, doc_type)

            if doc_type == DocumentType.AADHAAR_FRONT:
                raw_text     = KYCService.extract_text(tmp_path, lang="eng+hin")
                ocr_result   = KYCService.process_aadhaar(raw_text, user)
                ocr_verified = ocr_result["comparison"]["verified"]

            elif doc_type == DocumentType.AADHAAR_BACK:
                raw_text     = KYCService.extract_text(tmp_path, lang="eng+hin")
                ocr_result   = KYCService.process_aadhaar_back(raw_text, user)
                ocr_verified = True

            elif doc_type == DocumentType.PAN_CARD:
                raw_text     = KYCService.extract_text(tmp_path)
                ocr_result   = KYCService.process_pan(raw_text, user)
                ocr_verified = ocr_result["comparison"]["verified"]

            elif doc_type in [DocumentType.SALARY_SLIP, DocumentType.BANK_STATEMENT]:
                if not bank_verification:
                    ocr_result = {
                        "extracted":      {},
                        "comparison":     {"verified": False, "name_score": 0},
                        "user_data":      {},
                        "failed_reasons": [
                            "No verified bank record found. Complete bank verification first."
                        ],
                    }
                    ocr_verified = False
                else:
                    raw_text = KYCService.extract_text(tmp_path)

                    if doc_type == DocumentType.BANK_STATEMENT:
                        # Bank statement: verify account number + account holder name
                        ocr_result   = KYCService.process_bank(raw_text, bank_verification)
                        ocr_verified = ocr_result["comparison"]["verified"]
                    else:
                        # Salary slip: verify employee name vs profile.full_name (PAN)
                        # NOT vs bank_verification.account_holder_name — PAN is source of truth
                        ocr_result   = KYCService.process_salary_slip(raw_text, user)
                        ocr_verified = ocr_result["comparison"]["verified"]

        except Exception as e:
            ocr_result = {
                "extracted":      {},
                "comparison":     {"verified": False, "name_score": 0},
                "user_data":      {},
                "failed_reasons": [f"OCR error: {str(e)}"],
            }
            ocr_verified = False

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        return ocr_result, ocr_verified, raw_text

    @staticmethod
    def _decide_status(ocr_verified: bool, ocr_result: dict) -> DocumentStatus:
        
        if ocr_verified:
            return DocumentStatus.APPROVED

        score = 0
        if ocr_result and "comparison" in ocr_result:
            score = ocr_result["comparison"].get("name_score", 0)

        if score >= SCORE_UNDER_REVIEW:
            return DocumentStatus.UNDER_REVIEW
        return DocumentStatus.REJECTED

    # =========================================================================
    # _process_single_document
    # =========================================================================

    @staticmethod
    def _process_single_document(
        db:                Session,
        user,
        doc_type:          DocumentType,
        file:              UploadFile,
        content:           bytes,
        bank_verification: Optional[object],
    ) -> dict:
       
        file_size = len(content)

        # 1. Validate
        DocumentUploadService._validate_file(file, doc_type, file_size)

        # 2. Remove existing record
        existing = DocumentUploadRepository.get_by_user_and_type(db, user.user_id, doc_type)
        if existing:
            if existing.status == DocumentStatus.APPROVED:
                raise HTTPException(400, f"{doc_type.value} is already approved and cannot be replaced.")
            DocumentUploadService._delete_from_cloudinary(existing.file_path)
            DocumentUploadRepository.delete_document(db, existing)

        # 3. Upload to Cloudinary
        file_url = DocumentUploadService._upload_to_cloudinary(user.user_id, doc_type, content)

        # 4. OCR — uses in-memory bytes, never downloads from Cloudinary
        ocr_result, ocr_verified, raw_text = DocumentUploadService._run_ocr(
            content           = content,
            doc_type          = doc_type,
            user              = user,
            bank_verification = bank_verification,
        )

        # 5. Status
        status      = DocumentUploadService._decide_status(ocr_verified, ocr_result)
        match_score = (
            ocr_result["comparison"].get("name_score")
            if ocr_result and "comparison" in ocr_result
            else None
        )

        # 6. Save
        document = DocumentUpload(
            user_id        = user.user_id,
            email          = user.email,
            document_type  = doc_type,
            file_name      = file.filename,
            file_path      = file_url,
            file_size      = file_size,
            mime_type      = file.content_type,
            status         = status,
            ocr_text       = raw_text or None,
            extracted_data = ocr_result,
            match_score    = match_score,
            ocr_verified   = 1 if ocr_verified else 0,
            uploaded_at    = datetime.now(timezone.utc),
            reviewed_at    = datetime.now(timezone.utc),
        )
        document = DocumentUploadRepository.create_document(db, document)

        # 7. Message
        failed_reasons = (ocr_result or {}).get("failed_reasons", [])
        if status == DocumentStatus.APPROVED:
            msg = f"{doc_type.value} verified and approved automatically."
        elif status == DocumentStatus.UNDER_REVIEW:
            msg = (
                f"{doc_type.value} requires manual admin review "
                f"(match score: {round(match_score or 0, 1)}). "
                f"Reasons: {'; '.join(failed_reasons)}"
            )
        else:
            msg = (
                f"{doc_type.value} rejected by OCR. "
                f"Reasons: {'; '.join(failed_reasons) if failed_reasons else 'Data mismatch.'}"
            )

        return {
            "document_type":  doc_type.value,
            "file_name":      document.file_name,
            "file_size":      document.file_size,
            "status":         document.status.value,
            "uploaded_at":    document.uploaded_at.isoformat(),
            "match_score":    match_score,
            "ocr_verified":   document.ocr_verified,
            "failed_reasons": failed_reasons,
            "message":        msg,
        }

    # =========================================================================
    # BULK UPLOAD
    # =========================================================================

    @staticmethod
    def bulk_upload_documents(
        db:            Session,
        user_id:       int,
        pan_card:      Optional[UploadFile],
        aadhaar_front: Optional[UploadFile],
        aadhaar_back:  Optional[UploadFile],
        income_proof:  Optional[UploadFile],
        income_type:   Optional[str] = None,
        file_bytes:    dict          = None,
    ) -> dict:

        if file_bytes is None:
            file_bytes = {}

        user = UserRepository.get_by_user_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")

        if user.pan_status != "VERIFIED" or user.aadhaar_status != "VERIFIED":
            raise HTTPException(400, "Complete PAN and Aadhaar verification before uploading documents.")
        if user.bank_status != "VERIFIED":
            raise HTTPException(400, "Complete bank verification before uploading documents.")

        bank_verification = DocumentUploadService._get_bank_verification(db, user.user_id)

        file_map = [
            ("pan_card",      pan_card,      DocumentType.PAN_CARD),
            ("aadhaar_front", aadhaar_front, DocumentType.AADHAAR_FRONT),
            ("aadhaar_back",  aadhaar_back,  DocumentType.AADHAAR_BACK),
        ]

        if income_proof and income_proof.filename:
            valid_income = [DocumentType.SALARY_SLIP.value, DocumentType.BANK_STATEMENT.value]
            if not income_type or income_type.upper() not in valid_income:
                raise HTTPException(400, {
                    "error":        "income_type is required when income_proof is provided",
                    "valid_values": valid_income,
                    "message":      "Set income_type to SALARY_SLIP or BANK_STATEMENT",
                })
            file_map.append(("income_proof", income_proof, DocumentType(income_type.upper())))

        uploaded_results = []
        skipped_approved = []
        skipped_empty    = []

        for field_name, file, doc_type in file_map:

            if not file or not file.filename:
                skipped_empty.append(doc_type.value)
                continue

            content = file_bytes.get(field_name)
            if not content:
                skipped_empty.append(doc_type.value)
                continue

            existing = DocumentUploadRepository.get_by_user_and_type(db, user.user_id, doc_type)
            if existing and existing.status == DocumentStatus.APPROVED:
                skipped_approved.append(doc_type.value)
                continue

            result = DocumentUploadService._process_single_document(
                db                = db,
                user              = user,
                doc_type          = doc_type,
                file              = file,
                content           = content,
                bank_verification = bank_verification,
            )
            uploaded_results.append(result)

        if not uploaded_results:
            raise HTTPException(400, {
                "error":            "Nothing to upload",
                "skipped_approved": skipped_approved,
                "message":          "All provided documents are already approved.",
            })

        user.document_status = "UPLOADED"
        UserRepository.save(db)

        all_docs = DocumentUploadRepository.get_by_user_id(db, user.user_id)
        DocumentUploadService._update_user_doc_status(db, user, all_docs)

        missing               = DocumentUploadService._check_missing(db, user.user_id)
        all_required_uploaded = len(missing) == 0

        return {
            "user_id":               user.user_id,
            "email":                 user.email,
            "uploaded_documents":    uploaded_results,
            "total_uploaded":        len(uploaded_results),
            "skipped_approved":      skipped_approved,
            "skipped_empty":         skipped_empty,
            "missing_documents":     missing,
            "all_required_uploaded": all_required_uploaded,
            "document_status":       user.document_status,
            "kyc_status":            user.kyc_status,
            "message": (
                "All required documents uploaded and OCR verified."
                if all_required_uploaded
                else f"Documents processed. Still missing: {', '.join(missing)}"
            ),
        }

    # =========================================================================
    # LIST DOCUMENTS
    # =========================================================================

    @staticmethod
    def list_documents(db: Session, user_id: int) -> dict:

        user = UserRepository.get_by_user_id(db, user_id)
        if not user:
            raise HTTPException(404, "User not found")

        documents = DocumentUploadRepository.get_by_user_id(db, user.user_id)

        doc_list = [
            {
                "id":             doc.id,
                "document_type":  doc.document_type.value,
                "file_name":      doc.file_name,
                "file_size":      doc.file_size,
                "status":         doc.status.value,
                "match_score":    doc.match_score,
                "ocr_verified":   doc.ocr_verified,
                "uploaded_at":    doc.uploaded_at.isoformat(),
                "reviewed_at":    doc.reviewed_at.isoformat() if doc.reviewed_at else None,
                "admin_remarks":  doc.admin_remarks,
                "failed_reasons": (doc.extracted_data or {}).get("failed_reasons", []),
            }
            for doc in documents
        ]

        uploaded_types = [doc.document_type for doc in documents]
        missing = []
        for req in DocumentUploadService.REQUIRED_DOCS:
            if req not in uploaded_types:
                missing.append(req.value)
        if not any(t in uploaded_types for t in DocumentUploadService.INCOME_PROOF_DOCS):
            missing.append("SALARY_SLIP or BANK_STATEMENT")

        approved_types = {doc.document_type for doc in documents if doc.status == DocumentStatus.APPROVED}
        all_approved   = (
            set(DocumentUploadService.REQUIRED_DOCS).issubset(approved_types) and
            bool(approved_types & set(DocumentUploadService.INCOME_PROOF_DOCS))
        )

        return {
            "user_id":            user.user_id,
            "email":              user.email,
            "documents":          doc_list,
            "total_documents":    len(doc_list),
            "required_documents": ["AADHAAR_FRONT", "AADHAAR_BACK", "PAN_CARD", "SALARY_SLIP or BANK_STATEMENT"],
            "missing_documents":  missing,
            "all_approved":       all_approved,
        }

    # =========================================================================
    # DELETE DOCUMENT
    # =========================================================================

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> dict:

        document = DocumentUploadRepository.get_by_id(db, document_id)
        if not document:
            raise HTTPException(404, "Document not found")
        if document.user_id != user_id:
            raise HTTPException(403, "Unauthorised: this document does not belong to you")
        if document.status == DocumentStatus.APPROVED:
            raise HTTPException(400, "Cannot delete an approved document")

        doc_type   = document.document_type.value
        doc_name   = document.file_name
        doc_status = document.status.value

        DocumentUploadService._delete_from_cloudinary(document.file_path)
        DocumentUploadRepository.delete_document(db, document)

        return {
            "message":         "Document deleted successfully",
            "document_id":     document_id,
            "document_type":   doc_type,
            "file_name":       doc_name,
            "previous_status": doc_status,
        }