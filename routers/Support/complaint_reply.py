from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from typing import List

from core.database import get_db

from core.dependencies import require_roles

from models.Auth.user import User

from schemas.Support.complaint_reply_schema import (

    ComplaintReplyCreate,

    ComplaintReplyResponse
)

from services.Support.complaint_reply_service import (

    add_complaint_reply_service,

    get_complaint_replies_service
)

router = APIRouter(

    prefix="/api/v1/complaint-replies",

    tags=["Complaint Replies"]
)


# =====================================================
# ADD REPLY
# =====================================================
@router.post(
    "/{complaint_id}",

    response_model=ComplaintReplyResponse
)
def add_reply(

    complaint_id: int,

    payload: ComplaintReplyCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "USER",
            "SUPPORT",
            "SUPER_ADMIN"
        )
    )
):

    return add_complaint_reply_service(

        db=db,

        complaint_id=complaint_id,

        message=payload.message,

        current_user=current_user
    )


# =====================================================
# GET REPLIES
# =====================================================
@router.get(
    "/{complaint_id}",

    response_model=List[
        ComplaintReplyResponse
    ]
)
def get_replies(

    complaint_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "USER",
            "SUPPORT",
            "SUPER_ADMIN"
        )
    )
):

    return get_complaint_replies_service(

        db,

        complaint_id
    )