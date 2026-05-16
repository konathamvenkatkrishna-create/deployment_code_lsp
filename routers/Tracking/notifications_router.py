from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.logger import logger
from core.dependencies import require_roles

from services.Tracking.notification_service import NotificationService
from schemas.Tracking.notification_schemas import NotificationResponse

from models.Auth.user import User


router = APIRouter(
    prefix="/loan",
    tags=["Notifications"]
)


# ------------------------------------------------
# GET USER NOTIFICATIONS (WITH PAGINATION)
# ------------------------------------------------
@router.get(
    "/notifications",
    response_model=List[NotificationResponse],
    operation_id="get_user_notifications"
)
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("USER", "ADMIN", "SUPER_ADMIN")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    try:
        logger.info(f"[GET NOTIFICATIONS] user={current_user.id}")

        notifications = NotificationService.get_user_notifications(
            db=db,
            user_id=current_user.id
        )

        # ✅ simple pagination
        return notifications[offset: offset + limit]

    except Exception as e:
        logger.error(
            f"[NOTIFICATION ERROR] user={current_user.id}, error={str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch notifications"
        )