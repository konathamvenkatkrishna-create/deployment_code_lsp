import uuid
from sqlalchemy import (Column,DateTime,Text,ForeignKey,Integer)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from core.database import Base


class NoDueCertificate(Base):
    __tablename__="ndc"
    id=Column(Integer , primary_key=True)
    application_id=Column(Integer,ForeignKey("loan_application.id"))
    pdf_url=Column(Text)
    issued_on=Column(DateTime,server_default=func.now())