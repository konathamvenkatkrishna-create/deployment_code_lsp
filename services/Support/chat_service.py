from sqlalchemy.orm import Session

from fastapi import HTTPException

from repositories.Support.chat_repository import (

    create_chat_message,

    get_chat_history_by_user
)

from schemas.Support.chat_schema import (
    ChatCreate
)

from models.Auth.user import (
    User
)


# =====================================================
# SEND CHAT MESSAGE
# =====================================================
def send_chat_message(

    db: Session,

    data: ChatCreate,

    current_user: User
):

    # =================================================
    # VALIDATE MESSAGE
    # =================================================
    if not data.message.strip():

        raise HTTPException(

            status_code=400,

            detail="Message cannot be empty"
        )

    # =================================================
    # DETERMINE SENDER
    # =================================================
    if current_user.role in [

        "ADMIN",

        "SUPER_ADMIN"
    ]:

        sender = "admin"

    else:

        sender = "user"

    # =================================================
    # CREATE MESSAGE
    # =================================================
    message = create_chat_message(

        db=db,

        user_id=
            current_user.id,

        message=
            data.message.strip(),

        sender=
            sender
    )

    return {

        "success":
            True,

        "message":
            "Chat message sent successfully",

        "data":
            message
    }


# =====================================================
# GET CHAT HISTORY
# =====================================================
def get_chat_history(

    db: Session,

    current_user: User
):

    chats = get_chat_history_by_user(

        db,

        current_user.id
    )

    return {

        "success":
            True,

        "count":
            len(chats),

        "data":
            chats
    }