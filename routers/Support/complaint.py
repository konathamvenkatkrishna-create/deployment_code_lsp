from typing import (
    List,
    Optional
)

from fastapi import (
    APIRouter,
    Depends,
    Form,
    File,
    UploadFile,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import (
    get_db
)

from core.dependencies import (
    require_roles
)

from models.Auth.user import (
    User
)

# ✅ ADD THIS IMPORT
from models.Loan_application.loan_application import (
    LoanApplication
)

from schemas.Support.complaint_schema import (

    ComplaintCreate,

    ComplaintResponse,

    ComplaintDetailResponse
)

from services.Support.complaint_service import (

    register_complaint,

    list_complaints,

    get_complaint_detail
)

from services.Support.cloudinary_upload_services import (
    upload_support_attachment
)

from core.enums import (

    ComplaintCategory,

    ComplaintPriority
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/support",

    tags=["Complaints"]
)


# =====================================================
# USER - CREATE COMPLAINT
# =====================================================
@router.post(
    "/complaint",

    response_model=ComplaintResponse
)
async def create_new_complaint(

    category: ComplaintCategory = Form(...),

    subject: str = Form(...),

    description: str = Form(...),

    priority: ComplaintPriority = Form(
        ComplaintPriority.MEDIUM
    ),

    attachment: Optional[
        UploadFile
    ] = File(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    ),
):

    try:

        # =========================================
        # FETCH USER LOAN APPLICATION
        # =========================================
        loan_application = db.query(
            LoanApplication
        ).filter(

            LoanApplication.user_profile_id
            == current_user.id

        ).order_by(
            LoanApplication.id.desc()
        ).first()

        if not loan_application:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No loan application found "
                    "for current user"
                )
            )

        # =========================================
        # VALIDATE SUBJECT
        # =========================================
        if not subject.strip():

            raise HTTPException(

                status_code=400,

                detail="Subject is required"
            )

        # =========================================
        # VALIDATE DESCRIPTION
        # =========================================
        if not description.strip():

            raise HTTPException(

                status_code=400,

                detail="Description is required"
            )

        attachment_url = None

        # =========================================
        # UPLOAD ATTACHMENT
        # =========================================
        if attachment:

            attachment_url = (
                await upload_support_attachment(

                    attachment=
                        attachment,

                    category=
                        category.value,

                    user_id=
                        current_user.id,

                    complaint_id=
                        0
                )
            )

        # =========================================
        # REQUEST PAYLOAD
        # =========================================
        data = ComplaintCreate(

            # ✅ AUTO APPLICATION ID
            application_id=
                loan_application.id,

            category=
                category,

            subject=
                subject.strip(),

            description=
                description.strip(),

            priority=
                priority,

            attachment_url=
                attachment_url
        )

        # =========================================
        # REGISTER COMPLAINT
        # =========================================
        complaint = register_complaint(

            db=db,

            payload=data,

            current_user=current_user,

            attachment_path=attachment_url
        )

        return complaint

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# USER - GET OWN COMPLAINTS
# =====================================================
@router.get(
    "/complaints",

    response_model=List[ComplaintResponse]
)
def get_complaint_list(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("USER")
    ),
):

    try:

        complaints = list_complaints(

            db,

            current_user
        )

        return complaints

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )

