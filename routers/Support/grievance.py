from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import (
    get_db
)

from schemas.Support.grievance_schema import (

    GrievanceOfficerCreate,

    GrievanceOfficerResponse
)

from services.Support.grievance_service import (

    fetch_grievance_officer,

    add_grievance_officer
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/support",

    tags=["Grievance Officer"]
)


# =====================================================
# GET GRIEVANCE OFFICER
# =====================================================
@router.get(
    "/grievance",

    response_model=GrievanceOfficerResponse
)
def get_grievance(

    db: Session = Depends(get_db)
):

    try:

        response = fetch_grievance_officer(
            db
        )

        return response["data"]

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# CREATE GRIEVANCE OFFICER
# =====================================================
@router.post(
    "/grievance",

    response_model=GrievanceOfficerResponse
)
def create_grievance(

    data: GrievanceOfficerCreate,

    db: Session = Depends(get_db)
):

    try:

        response = add_grievance_officer(

            db=db,

            data=data
        )

        return response["data"]

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )