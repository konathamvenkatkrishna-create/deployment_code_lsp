from pydantic import BaseModel, EmailStr

class AadhaarVerificationRequest(BaseModel):
    email: EmailStr

class AadhaarVerificationResponse(BaseModel):
    message: str
    aadhaar_status: str
    next_step: str