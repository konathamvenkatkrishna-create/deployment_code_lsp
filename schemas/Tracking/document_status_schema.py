# schemas/document_status_schema.py

from pydantic import BaseModel
from typing import Optional


class DocumentItem(BaseModel):
    document_type: str
    status: str
    reason: Optional[str] = None
    action: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    application_id: int
    application_status: str
    documents: list[DocumentItem]