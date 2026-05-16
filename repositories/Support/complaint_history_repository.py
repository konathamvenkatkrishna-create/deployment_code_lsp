from sqlalchemy.orm import Session
from models.Support.complaint_history import ComplaintHistory


def create_complaint_history(
    db: Session,
    complaint_id: int,
    old_status: str | None,
    new_status: str,
    comment: str | None,
    changed_by: str,
):
    history = ComplaintHistory(
        complaint_id=complaint_id,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
        changed_by=changed_by,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history