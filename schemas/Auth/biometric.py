from pydantic import BaseModel
from typing import Literal
class EnableBiometricSchema(BaseModel):
    device_id: str
    biometric_type: Literal["fingerprint", "face_id"]
    biometric_key: str 
class BiometricLoginSchema(BaseModel):
    mobile_number: str 
    device_id: str 
    biometric_type: Literal["fingerprint", "face_id"]
    biometric_signature: str 
class DisableBiometricSchema(BaseModel):
    device_id: str 
    biometric_type: Literal["fingerprint", "face_id"]

class VerifyBiometricOTPSchema(BaseModel):
    mobile_number: str 
    otp: str 
    device_id: str 