from sqlalchemy import Column, Integer, String
from core.database import Base


class Grievance(Base):
    __tablename__ = "grievance_officer"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    designation = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    office_address = Column(String, nullable=False)
    working_hours = Column(String, nullable=False)

