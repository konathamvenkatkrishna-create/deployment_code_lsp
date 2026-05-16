from pydantic import BaseModel


class GrievanceOfficerCreate(BaseModel):
    name: str
    designation: str
    email: str
    phone: str
    office_address: str
    working_hours: str


class GrievanceOfficerResponse(GrievanceOfficerCreate):
    id: int

    class Config:
        from_attributes = True

