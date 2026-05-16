from pydantic import BaseModel


class FAQResponse(BaseModel):
    id: int
    category: str
    question: str
    answer: str
    is_active: bool

    class Config:
        from_attributes = True