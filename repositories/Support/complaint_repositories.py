import uuid
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from models.Support.complaint import Complaint
from schemas.Support.complaint_schema import ComplaintCreate


def generate_complaint_number() -> str:
    return f"CMP-{uuid.uuid4().hex[:10].upper()}"


def create_complaint(
    db: Session,
    user_id: int,
    data: ComplaintCreate,
    commit: bool = True,
):
    max_attempts = 5

    for _ in range(max_attempts):
        try:
            complaint = Complaint(
                complaint_number=generate_complaint_number(),
                user_id=user_id,
                application_id=data.application_id,
                category=data.category.value if hasattr(data.category, "value") else data.category,
                subject=data.subject,
                description=data.description,
                priority=data.priority.value if hasattr(data.priority, "value") else data.priority,
                attachment_url=data.attachment_url,
                status="Open",
            )

            db.add(complaint)
            db.flush()

            if commit:
                db.commit()
                db.refresh(complaint)

            return complaint

        except IntegrityError:
            db.rollback()

    raise ValueError("Unable to generate unique complaint number after multiple attempts")


def get_user_complaints(db: Session, user_id: int):
    return (
        db.query(Complaint)
        .filter(Complaint.user_id == user_id)
        .order_by(Complaint.created_at.desc())
        .all()
    )


def get_user_complaint_by_id(db: Session, complaint_id: int, user_id: int):
    return (
        db.query(Complaint)
        .options(joinedload(Complaint.history))
        .filter(
            Complaint.id == complaint_id,
            Complaint.user_id == user_id,
        )
        .first()
    )


def update_complaint_status(
    db: Session,
    complaint: Complaint,
    status: str,
    commit: bool = True,
):
    complaint.status = status
    db.flush()

    if commit:
        db.commit()
        db.refresh(complaint)

    return complaint


def reopen_complaint(
    db: Session,
    complaint: Complaint,
    commit: bool = True,
):
    complaint.status = "Open"
    complaint.escalated = True
    db.flush()

    if commit:
        db.commit()
        db.refresh(complaint)

    return complaint