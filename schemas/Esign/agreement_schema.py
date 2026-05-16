from pydantic import BaseModel, Field
from typing import Optional


class AgreementRequest(BaseModel):
    loan_id: int = Field(..., gt=0)


class AgreementResponse(BaseModel):
    exists: bool
    loan_id: int
    pdf_path: str
    status: str
    provider_ref: Optional[str] = None
    signed_pdf_path: Optional[str] = None