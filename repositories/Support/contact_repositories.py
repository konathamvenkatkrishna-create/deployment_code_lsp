from sqlalchemy.orm import Session
from models.Support.contact import ContactMessage
from schemas.Support.contact_schema import ContactCreate


def create_contact_message(db: Session, data: ContactCreate):
    contact = ContactMessage(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact