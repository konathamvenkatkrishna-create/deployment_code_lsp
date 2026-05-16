# app/schemas/webhook_schema.py

from pydantic import BaseModel
from typing import Optional, Dict

class NBFCWebhookRequest(BaseModel):
    event_id: str 
    application_id: int
    status: str
    payload: Optional[Dict] = None


class NBFCWebhookResponse(BaseModel):
    success: bool
    message: str