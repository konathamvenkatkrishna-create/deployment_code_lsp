from pydantic import BaseModel
from typing import Optional


class EsignCallbackRequest(BaseModel):
    transaction_id: str
    status: str
    signed_pdf_url: Optional[str] = None