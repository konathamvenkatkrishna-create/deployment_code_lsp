from pydantic import BaseModel
from enum import Enum
class ConsentType(str, Enum):
    TERMS = "Terms & Conditions"
    DATA = "Data Consent"
    CREDIT = "Credit Bureau Consent"
    PRIVACY = "Privacy Policy"
 
class ConsentMasterCreate(BaseModel):
    type: str
    version: str
    content: str
    active: bool = True
 
class UserConsentRequest(BaseModel):
    consent_type: ConsentType                
    accepted: bool                    
    scroll_completed: bool
 