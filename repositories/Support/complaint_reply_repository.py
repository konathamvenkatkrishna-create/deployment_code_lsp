from sqlalchemy.orm import Session

from models.Support.complaint_reply import ComplaintReply


def create_reply_repo(
    db: Session,
    complaint_id: int,
    sender_type: str,
    sender_id: int,
    message: str
):

    reply = ComplaintReply(

        complaint_id=complaint_id,

        sender_type=sender_type,

        sender_id=sender_id,

        message=message
    )

    db.add(reply)

    db.commit()

    db.refresh(reply)

    return reply


def get_complaint_replies_repo(
    db: Session,
    complaint_id: int
):

    return db.query(
        ComplaintReply
    ).filter(
        ComplaintReply.complaint_id == complaint_id
    ).order_by(
        ComplaintReply.created_at.asc()
    ).all()