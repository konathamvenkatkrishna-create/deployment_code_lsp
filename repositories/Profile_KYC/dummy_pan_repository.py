from sqlalchemy.orm import Session
from models.Profile_KYC.dummy_pan import DummyPAN
from typing import Optional

class DummyPANRepository:
    
    @staticmethod
    def get_by_pan_number(db: Session, pan_number: str) -> Optional[DummyPAN]:
        return db.query(DummyPAN).filter(DummyPAN.pan_number == pan_number).first()
    
    @staticmethod
    def get_by_aadhaar_number(db: Session, aadhaar_number: str) -> Optional[DummyPAN]:
        return db.query(DummyPAN).filter(DummyPAN.aadhaar_number == aadhaar_number).first()
    
    @staticmethod
    def create_dummy_pan(db: Session, pan: DummyPAN) -> DummyPAN:
        db.add(pan)
        db.commit()
        db.refresh(pan)
        return pan