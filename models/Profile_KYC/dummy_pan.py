from sqlalchemy import Column, String, Date, Index
from core.database import Base

class DummyPAN(Base):
    __tablename__ = "dummy_pans"

    pan_number = Column(String(10), primary_key=True)
    aadhaar_number = Column(String(12), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    dob = Column(Date, nullable=False)
    address = Column(String, nullable=False)
    gender = Column(String(10), nullable=False)
    
    __table_args__ = (
        Index('idx_aadhaar_lookup', 'aadhaar_number'),
    )