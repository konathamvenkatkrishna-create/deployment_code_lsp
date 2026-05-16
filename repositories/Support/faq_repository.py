from sqlalchemy.orm import Session
from models.Support.faq import FAQ


def get_all_active_faqs(db: Session):
    return db.query(FAQ).filter(FAQ.is_active == True).all()