from fastapi import HTTPException

from sqlalchemy.orm import Session

from repositories.Support.grievance_repository import (

    get_grievance_officer,

    create_grievance_officer
)

from schemas.Support.grievance_schema import (
    GrievanceOfficerCreate
)


# =====================================================
# FETCH GRIEVANCE OFFICER
# =====================================================
def fetch_grievance_officer(

    db: Session
):

    try:

        officer = get_grievance_officer(
            db
        )

        if not officer:

            raise HTTPException(

                status_code=404,

                detail=(
                    "Grievance officer "
                    "details not found"
                )
            )

        return {

            "success":
                True,

            "data":
                officer
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# ADD GRIEVANCE OFFICER
# =====================================================
def add_grievance_officer(

    db: Session,

    data: GrievanceOfficerCreate
):

    # =============================================
    # VALIDATE NAME
    # =============================================
    if not data.name.strip():

        raise HTTPException(

            status_code=400,

            detail="Officer name is required"
        )

    # =============================================
    # VALIDATE EMAIL
    # =============================================
    if not data.email.strip():

        raise HTTPException(

            status_code=400,

            detail="Officer email is required"
        )

    # =============================================
    # VALIDATE PHONE
    # =============================================
    if not data.phone.strip():

        raise HTTPException(

            status_code=400,

            detail="Officer phone is required"
        )

    try:

        officer = create_grievance_officer(

            db=db,

            data=data
        )

        return {

            "success":
                True,

            "message":
                "Grievance officer added successfully",

            "data":
                officer
        }

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )