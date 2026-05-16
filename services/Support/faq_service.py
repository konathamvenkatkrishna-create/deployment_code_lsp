from sqlalchemy.orm import Session

from fastapi import HTTPException

from repositories.Support.faq_repository import (
    get_all_active_faqs
)


# =====================================================
# LIST ACTIVE FAQS
# =====================================================
def list_faqs(

    db: Session
):

    try:

        faqs = get_all_active_faqs(
            db
        )

        return {

            "success":
                True,

            "count":
                len(faqs),

            "data":
                faqs
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )