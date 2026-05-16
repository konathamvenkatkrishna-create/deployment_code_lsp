from uuid import UUID
from datetime import datetime
from typing import Optional
from schemas.Loan_application.base import BaseSchema


class NoDueCertificateSchema(BaseSchema):
    loan_id: UUID
    pdf_url: str
    issued_on: Optional[datetime] = None
