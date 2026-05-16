from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from typing import List

from core.database import (
    get_db
)

from core.dependencies import (
    require_roles
)

from models.Auth.user import (
    User
)

from schemas.Support.chat_schema import (

    ChatCreate,

    ChatResponse
)

from services.Support.chat_service import (

    send_chat_message,

    get_chat_history
)


# =====================================================
# ROUTER
# =====================================================
router = APIRouter(

    prefix="/support/chat",

    tags=["Support Chat"]
)


# =====================================================
# SEND CHAT MESSAGE
# =====================================================
@router.post(
    "/message",

    response_model=ChatResponse
)
def post_chat_message(

    data: ChatCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "USER",
            "ADMIN",
            "SUPER_ADMIN"
        )
    )
):

    try:

        response = send_chat_message(

            db=db,

            data=data,

            current_user=current_user
        )

        return response["data"]

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )


# =====================================================
# GET CHAT HISTORY
# =====================================================
@router.get(
    "/history",

    response_model=List[ChatResponse]
)
def fetch_chat_history(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "USER",
            "ADMIN",
            "SUPER_ADMIN"
        )
    )
):

    try:

        response = get_chat_history(

            db=db,

            current_user=current_user
        )

        return response["data"]

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)
        )