from pydantic import BaseModel
from typing import Dict, Any


class RazorpayWebhookSchema(BaseModel):
    event: str
    payload: Dict[str, Any]