from pydantic import BaseModel, EmailStr

class PANVerificationRequest(BaseModel):
    email: EmailStr

class PANVerificationResponse(BaseModel):
    message: str
    pan_status: str
    next_step: str


    