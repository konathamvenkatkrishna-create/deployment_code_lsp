from sqlalchemy.orm import Session

from fastapi import HTTPException

from repositories.Support.contact_repositories import (
    create_contact_message
)

from schemas.Support.contact_schema import (
    ContactCreate
)


# =====================================================
# CREATE CONTACT MESSAGE
# =====================================================
def create_contact(

    db: Session,

    data: ContactCreate
):

    # =============================================
    # VALIDATE NAME
    # =============================================
    if not data.name.strip():

        raise HTTPException(

            status_code=400,

            detail="Name is required"
        )

    # =============================================
    # VALIDATE SUBJECT
    # =============================================
    if not data.subject.strip():

        raise HTTPException(

            status_code=400,

            detail="Subject is required"
        )

    # =============================================
    # VALIDATE MESSAGE
    # =============================================
    if not data.message.strip():

        raise HTTPException(

            status_code=400,

            detail="Message is required"
        )

    try:

        # =========================================
        # SAVE CONTACT MESSAGE
        # =========================================
        contact = create_contact_message(

            db=db,

            data=data
        )

        return {

            "success":
                True,

            "message":
                "Contact message submitted successfully",

            "data":
                contact
        }

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )