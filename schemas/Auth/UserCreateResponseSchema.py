from pydantic import BaseModel,EmailStr


class UserCreateSchema(BaseModel):
    mobile_number: str
    password: str
    username: str
    email:EmailStr

class UserResponseSchema(BaseModel):
    id: int
    mobile_number: str
    username: str

    class Config:
        from_attributes = True
