from pydantic import BaseModel, Field, field_validator
 
class BankVerificationRequest(BaseModel):
    account_number: str = Field(..., min_length=8,  max_length=20)
    account_holder_name: str = Field(..., min_length=2,  max_length=150)
    bank_name: str = Field(..., min_length=3,  max_length=100)
    ifsc: str = Field(..., min_length=11, max_length=11)
 
    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Account number must contain only digits")
        if len(v) < 8 or len(v) > 20:
            raise ValueError("Account number must be between 8–20 digits")
        return v
    @field_validator("ifsc")
    @classmethod
    def validate_ifsc(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 11:
            raise ValueError("IFSC code must be exactly 11 characters")
        if not v[:4].isalpha():
            raise ValueError("First 4 characters of IFSC must be letters")
        if v[4] != "0":
            raise ValueError("5th character of IFSC must be '0'")
        if not v[5:].isalnum():
            raise ValueError("Last 6 characters of IFSC must be alphanumeric")
        return v
 
    @field_validator("account_holder_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Account holder name must be at least 2 characters")
        return v
 
    @field_validator("bank_name")
    @classmethod
    def validate_bank_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Bank name must be at least 3 characters")
        return v
 

class BankUpdateRequest(BaseModel):

    account_number:str | None = Field(default=None, min_length=8,  max_length=20)
    account_holder_name: str | None = Field(default=None, min_length=2,  max_length=150)
    bank_name: str | None = Field(default=None, min_length=3,  max_length=100)
    ifsc: str | None = Field(default=None, min_length=11, max_length=11)
 
    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Account number must contain only digits")
        if len(v) < 8 or len(v) > 20:
            raise ValueError("Account number must be between 8–20 digits")
        return v
 
    @field_validator("ifsc")
    @classmethod
    def validate_ifsc(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) != 11:
            raise ValueError("IFSC code must be exactly 11 characters")
        if not v[:4].isalpha():
            raise ValueError("First 4 characters of IFSC must be letters")
        if v[4] != "0":
            raise ValueError("5th character of IFSC must be '0'")
        if not v[5:].isalnum():
            raise ValueError("Last 6 characters of IFSC must be alphanumeric")
        return v
 
    @field_validator("account_holder_name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Account holder name must be at least 2 characters")
        return v
 
    @field_validator("bank_name")
    @classmethod
    def validate_bank_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Bank name must be at least 3 characters")
        return v
 
class BankVerificationResponse(BaseModel):
    message: str
    next:    str
 