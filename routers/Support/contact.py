from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import (
    get_db
)

from schemas.Support.contact_schema import (

    ContactCreate,

    ContactResponse
)

from services.Support.contact_service import (
    create_contact
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/support",

    tags=["Contact Support"]
)


# =====================================================
# SUBMIT CONTACT FORM
# =====================================================
@router.post(
    "/contact",

    response_model=ContactResponse
)
def submit_contact(

    data: ContactCreate,

    db: Session = Depends(get_db)
):

    try:

        response = create_contact(

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