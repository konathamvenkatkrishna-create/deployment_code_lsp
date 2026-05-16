from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class IncomeTypeEnum(str, Enum):
    SALARY_SLIP    = "SALARY_SLIP"
    BANK_STATEMENT = "BANK_STATEMENT"

class DocumentStatusEnum(str, Enum):
    UPLOADED     = "UPLOADED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED     = "APPROVED"
    REJECTED     = "REJECTED"

class ReviewAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT  = "REJECT"

class SingleDocumentResult(BaseModel):
    document_type:  str
    file_name:      str
    file_size:      int
    status:         str
    uploaded_at:    datetime
    match_score:    Optional[float] = None
    ocr_verified:   Optional[int]   = None   # 1 = passed, 0 = failed
    failed_reasons: List[str]       = []
    message:        str

class BulkDocumentUploadResponse(BaseModel):
    user_id:               int
    email:                 str
    uploaded_documents:    List[SingleDocumentResult]
    total_uploaded:        int
    skipped_approved:      List[str]   
    skipped_empty:         List[str]  
    missing_documents:     List[str]  
    all_required_uploaded: bool
    document_status:       str
    kyc_status:            str
    message:               str

class DocumentListItem(BaseModel):
    id:             int
    document_type:  str
    file_name:      str
    file_size:      int
    status:         str
    match_score:    Optional[float] = None
    ocr_verified:   Optional[int]   = None
    uploaded_at:    datetime
    reviewed_at:    Optional[datetime]   = None
    admin_remarks:  Optional[str]   = None
    failed_reasons: List[str]       = []

class AllDocumentsResponse(BaseModel):
    user_id:            int
    email:              str
    documents:          List[DocumentListItem]
    total_documents:    int
    required_documents: List[str]
    missing_documents:  List[str]
    all_approved:       bool

# ── Admin ──────────────────────────────────────────────────────────────────────

class DocumentApprovalRequest(BaseModel):
    document_id:   int
    status:        DocumentStatusEnum
    admin_remarks: Optional[str] = None

class DocumentApprovalResponse(BaseModel):
    message:         str
    document_id:     int
    new_status:      str
    user_email:      str
    user_kyc_status: str

class PendingDocumentItem(BaseModel):
    id:            int
    user_id:       int
    email:         str
    document_type: str
    file_name:     str
    file_path:     str
    file_size:     int
    match_score:   Optional[float] = None
    uploaded_at:   str
    status:        str

class PendingDocumentsResponse(BaseModel):
    pending_documents: List[PendingDocumentItem]
    total_pending:     int

class DocumentReviewResponse(BaseModel):
    document_id:   int
    document_type: str
    user_email:    str
    status:        str
    message:       str
    kyc_completed: bool = False

class UserKYCDetails(BaseModel):
    user_id:             int
    email:               str
    full_name:           str
    pan_number:          str
    aadhaar_number:      str
    pan_status:          str
    aadhaar_status:      str
    bank_status:         str
    document_status:     str
    kyc_status:          str
    created_at:          datetime
    pan_verified_at:     Optional[datetime] = None
    aadhaar_verified_at: Optional[datetime] = None
    bank_verified_at:    Optional[datetime] = None