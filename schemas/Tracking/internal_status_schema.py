from pydantic import BaseModel


class InternalStatusUpdateRequest(BaseModel):
    application_id: int
    user_id: int
    status: str
    comment: str | None = None


class InternalStatusUpdateResponse(BaseModel):
    success: bool
    message: str