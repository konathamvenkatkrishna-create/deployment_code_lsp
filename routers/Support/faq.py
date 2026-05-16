from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from core.database import (
    get_db
)

from schemas.Support.faq_schema import (
    FAQResponse
)

from services.Support.faq_service import (
    list_faqs
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/api/v1/support/faqs",

    tags=["FAQs"]
)


# =====================================================
# GET ALL FAQS
# =====================================================
@router.get(
    "/",

    response_model=List[FAQResponse]
)
def get_faqs(

    db: Session = Depends(get_db)
):

    try:

        response = list_faqs(
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