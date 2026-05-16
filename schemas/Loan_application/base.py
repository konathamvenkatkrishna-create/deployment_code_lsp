from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    class Config:
        from_attributes = True

class MySchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {...}
        }
    )