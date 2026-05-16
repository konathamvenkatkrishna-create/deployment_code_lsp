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
    ComplaintDetailResponse
)

from services.Support.complaint_service import (

    admin_list_all_complaints_grouped_by_user,

    admin_get_complaint_detail,

    support_list_all_complaints
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/super-admin/support",

    tags=["SuperAdmin Complaints Dashboard"]
)


# =====================================================
# DASHBOARD SUMMARY
# =====================================================
@router.get("/dashboard")
def super_admin_dashboard_summary(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("SUPER_ADMIN")
    ),
):

    try:

        data = support_list_all_complaints(

            db,

            current_user
        )

        return {

            "success":
                True,

            "message":
                "Dashboard fetched successfully",

            "data":
                data
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# GET ALL COMPLAINTS GROUPED BY USER
# =====================================================
@router.get("/complaints")
def super_admin_get_all_complaints_grouped(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("SUPER_ADMIN")
    ),
):

    try:

        complaints = (
            admin_list_all_complaints_grouped_by_user(

                db,

                current_user
            )
        )

        return {

            "success":
                True,

            "message":
                "Complaints fetched successfully",

            "data":
                complaints
        }

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
def super_admin_get_single_complaint(

    complaint_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles("SUPER_ADMIN")
    ),
):

    try:

        complaint = admin_get_complaint_detail(

            db,

            complaint_id,

            current_user
        )

        return complaint

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )