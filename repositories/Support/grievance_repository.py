from sqlalchemy.orm import Session
from models.Support.grievance import Grievance
from schemas.Support.grievance_schema import GrievanceOfficerCreate


def create_grievance_officer(db: Session, data: GrievanceOfficerCreate):
    officer = Grievance(**data.model_dump())
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return officer


def get_grievance_officer(db: Session):
    return db.query(Grievance).first()