from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Form
)

from sqlalchemy.orm import Session

from typing import (
    Optional,
    List
)

from datetime import (
    datetime,
    timezone
)

from core.database import (
    get_db
)

from core.dependencies import (
    require_roles
)

from models.Auth.user import (
    User
)

from models.Profile_KYC.document_upload import (
    DocumentStatus
)

from repositories.Profile_KYC.user_repository import (
    UserRepository
)

from repositories.Profile_KYC.document_upload_repository import (
    DocumentUploadRepository
)

from schemas.Profile_KYC.document_schema import (

    DocumentReviewResponse,

    UserKYCDetails,

    ReviewAction
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/admin",

    tags=["Admin Panel"]
)


# =====================================================
# REVIEW DOCUMENT
# =====================================================
@router.post(
    "/documents/review",

    response_model=DocumentReviewResponse
)
def review_document(

    document_id: int = Form(...),

    action: ReviewAction = Form(...),

    admin_remarks: Optional[str] = Form(None),

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_roles("SUPER_ADMIN")
    ),
):

    try:

        document = DocumentUploadRepository.get_by_id(

            db,

            document_id
        )

        if not document:

            raise HTTPException(

                status_code=404,

                detail=f"Document {document_id} not found"
            )

        # =========================================
        # ALREADY APPROVED
        # =========================================
        if document.status == DocumentStatus.APPROVED:

            raise HTTPException(

                status_code=400,

                detail="Document already approved"
            )

        # =========================================
        # REJECT
        # =========================================
        if action.value == "REJECT":

            if (

                not admin_remarks

                or not admin_remarks.strip()
            ):

                raise HTTPException(

                    status_code=400,

                    detail=(
                        "Admin remarks required "
                        "for rejection"
                    )
                )

            document.status = DocumentStatus.REJECTED

            message = (
                f"Document rejected: "
                f"{admin_remarks}"
            )

        # =========================================
        # APPROVE
        # =========================================
        else:

            document.status = DocumentStatus.APPROVED

            message = (
                "Document approved successfully"
            )

        document.admin_remarks = admin_remarks

        document.reviewed_at = datetime.now(
            timezone.utc
        )

        document.reviewed_by = (
            current_admin.username
        )

        # =========================================
        # PROFILE UPDATE
        # =========================================
        profile = UserRepository.get_by_user_id(

            db,

            document.user_id
        )

        kyc_completed = False

        if profile:

            all_docs = (
                DocumentUploadRepository.get_by_user_id(

                    db,

                    profile.user_id
                )
            )

            verified_or_approved = {
                DocumentStatus.APPROVED
            }

            required_identity = [

                "AADHAAR_FRONT",

                "AADHAAR_BACK",

                "PAN_CARD"
            ]

            income_docs = [

                "SALARY_SLIP",

                "BANK_STATEMENT"
            ]

            identity_done = all(

                any(

                    d.document_type.value == req

                    and d.status in verified_or_approved

                    for d in all_docs
                )

                for req in required_identity
            )

            income_done = any(

                d.document_type.value in income_docs

                and d.status in verified_or_approved

                for d in all_docs
            )

            if identity_done and income_done:

                profile.document_status = "APPROVED"

                if (

                    profile.pan_status == "VERIFIED"

                    and profile.aadhaar_status == "VERIFIED"

                    and profile.bank_status == "VERIFIED"
                ):

                    profile.kyc_status = "COMPLETED"

                    kyc_completed = True

            else:

                profile.document_status = "UPLOADED"

        # =========================================
        # SAVE
        # =========================================
        DocumentUploadRepository.update_document(

            db,

            document
        )

        if profile:

            UserRepository.update_user(

                db,

                profile
            )

        return DocumentReviewResponse(

            document_id=
                document.id,

            document_type=
                document.document_type.value,

            user_email=
                document.email,

            status=
                document.status.value,

            message=
                message,

            kyc_completed=
                kyc_completed
        )

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                f"Failed to review document: "
                f"{str(e)}"
            )
        )


# =====================================================
# DOCUMENT STATS
# =====================================================
@router.get("/stats/documents")
def get_document_stats(

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_roles("SUPER_ADMIN")
    )
):

    total_docs = (
        DocumentUploadRepository.count_all(db)
    )

    uploaded = (
        DocumentUploadRepository.count_by_status(
            db,
            DocumentStatus.UPLOADED
        )
    )

    under_review = (
        DocumentUploadRepository.count_by_status(
            db,
            DocumentStatus.UNDER_REVIEW
        )
    )

    approved = (
        DocumentUploadRepository.count_by_status(
            db,
            DocumentStatus.APPROVED
        )
    )

    rejected = (
        DocumentUploadRepository.count_by_status(
            db,
            DocumentStatus.REJECTED
        )
    )

    return {

        "total_documents":
            total_docs,

        "uploaded":
            uploaded,

        "under_review":
            under_review,

        "approved":
            approved,

        "rejected":
            rejected,

        "pending_review":
            uploaded + under_review
    }


# =====================================================
# KYC STATS
# =====================================================
@router.get("/stats/kyc")
def get_kyc_stats(

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_roles("SUPER_ADMIN")
    )
):

    total_users = (
        UserRepository.count_all_users(db)
    )

    completed = (
        UserRepository.count_by_kyc_status(
            db,
            "COMPLETED"
        )
    )

    incomplete = (
        UserRepository.count_by_kyc_status(
            db,
            "INCOMPLETE"
        )
    )

    blocked = (
        UserRepository.count_by_kyc_status(
            db,
            "BLOCKED"
        )
    )

    return {

        "total_users":
            total_users,

        "kyc_completed":
            completed,

        "kyc_incomplete":
            incomplete,

        "kyc_blocked":
            blocked,

        "completion_rate":
            (
                f"{(completed / total_users * 100):.1f}%"
                if total_users > 0
                else "0%"
            )
    }


# =====================================================
# GET ALL USERS
# =====================================================
@router.get(
    "/users",

    response_model=List[UserKYCDetails]
)
def get_all_users(

    kyc_status: Optional[str] = Query(None),

    limit: int = Query(
        50,
        ge=1,
        le=100
    ),

    offset: int = Query(
        0,
        ge=0
    ),

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_roles("SUPER_ADMIN")
    ),
):

    if kyc_status:

        if kyc_status not in [

            "COMPLETED",

            "INCOMPLETE",

            "BLOCKED"
        ]:

            raise HTTPException(

                status_code=400,

                detail="Invalid kyc_status filter"
            )

        users = (
            UserRepository.get_users_by_kyc_status(

                db,

                kyc_status,

                limit,

                offset
            )
        )

    else:

        users = UserRepository.get_all_users(

            db,

            limit,

            offset
        )

    return users


# =====================================================
# GET SINGLE USER DETAILS
# =====================================================
@router.get("/users/{user_id}")
def get_user_details(

    user_id: int,

    db: Session = Depends(get_db),

    current_admin: User = Depends(
        require_roles("SUPER_ADMIN")
    )
):

    user = UserRepository.get_by_user_id(

        db,

        user_id
    )

    if not user:

        raise HTTPException(

            status_code=404,

            detail=f"User {user_id} not found"
        )

    documents = (
        DocumentUploadRepository.get_by_user_id(

            db,

            user_id
        )
    )

    return {

        "user":
            user,

        "documents": [

            {

                "id":
                    doc.id,

                "document_type":
                    doc.document_type.value,

                "file_name":
                    doc.file_name,

                "file_size":
                    doc.file_size,

                "status":
                    doc.status.value,

                "match_score":
                    doc.match_score,

                "ocr_verified":
                    doc.ocr_verified,

                "uploaded_at":
                    (
                        doc.uploaded_at.isoformat()
                        if doc.uploaded_at
                        else None
                    ),

                "reviewed_at":
                    (
                        doc.reviewed_at.isoformat()
                        if doc.reviewed_at
                        else None
                    ),

                "admin_remarks":
                    doc.admin_remarks,
            }

            for doc in documents
        ],

        "total_documents":
            len(documents)
    }