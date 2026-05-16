from fastapi import (
    APIRouter,
    Depends,
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

from schemas.Support.complaint_schema import (

    ComplaintDetailResponse,

    ComplaintStatusUpdate
)

from services.Support.complaint_service import (

    support_list_all_complaints,

    support_get_complaint_detail,

    support_update_complaint_status
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/support-team",

    tags=["Support Team Dashboard"]
)


# =====================================================
# GET ALL COMPLAINTS
# =====================================================
@router.get("/complaints")
def support_get_all_complaints(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "SUPPORT",
            "SUPER_ADMIN"
        )
    ),
):

    try:

        return support_list_all_complaints(

            db,

            current_user
        )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# GET SINGLE COMPLAINT
# =====================================================
@router.get(
    "/complaint/{complaint_id}",

    response_model=ComplaintDetailResponse
)
def support_get_single_complaint(

    complaint_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "SUPPORT",
            "SUPER_ADMIN"
        )
    ),
):

    try:

        return support_get_complaint_detail(

            db,

            complaint_id,

            current_user
        )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# UPDATE COMPLAINT STATUS
# =====================================================
@router.put(
    "/complaint/{complaint_id}/status"
)
def support_change_complaint_status(

    complaint_id: int,

    payload: ComplaintStatusUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("SUPPORT")
    ),
):

    try:

        return support_update_complaint_status(

            db=db,

            complaint_id=complaint_id,

            payload=payload,

            current_user=current_user
        )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )