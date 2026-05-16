from fastapi import HTTPException

from sqlalchemy.orm import Session

from models.Support.complaint import Complaint

from repositories.Support.complaint_reply_repository import (

    create_reply_repo,

    get_complaint_replies_repo
)


# =====================================================
# ADD REPLY
# =====================================================
def add_complaint_reply_service(

    db: Session,

    complaint_id: int,

    message: str,

    current_user
):

    complaint = db.query(
        Complaint
    ).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:

        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    # CLOSED complaints cannot reply
    if complaint.status == "CLOSED":

        raise HTTPException(
            status_code=400,
            detail="Complaint already closed"
        )

    sender_type = "USER"

    if current_user.role in [
        "SUPPORT",
        "SUPER_ADMIN"
    ]:
        sender_type = "SUPPORT"

    reply = create_reply_repo(

        db=db,

        complaint_id=complaint_id,

        sender_type=sender_type,

        sender_id=current_user.id,

        message=message
    )

    # reopen if user replied after resolved
    if (
        sender_type == "USER"
        and complaint.status == "RESOLVED"
    ):

        complaint.status = "IN_PROGRESS"

        db.commit()

    return reply


# =====================================================
# GET REPLIES
# =====================================================
def get_complaint_replies_service(

    db: Session,

    complaint_id: int
):

    return get_complaint_replies_repo(

        db,

        complaint_id
    )