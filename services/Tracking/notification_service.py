from sqlalchemy.orm import Session
from core.config import settings
from core.logger import logger

from repositories.Tracking.notification_repo import NotificationRepository


class NotificationService:

    # =====================================================
    # INTERNAL CREATE (COMMON METHOD)
    # =====================================================
    @staticmethod
    def _create_notification(db: Session, data: dict):
        try:
            notification = NotificationRepository.create(db, data)
            logger.info(f"[NOTIFICATION SENT] user_id={data['user_id']}, type={data['type']}")
            return notification

        except Exception as e:
            logger.error(f"[NOTIFICATION ERROR] {str(e)}")

            data["status"] = "FAILED"

            try:
                return NotificationRepository.create(db, data)
            except Exception as inner:
                logger.critical(f"[NOTIFICATION FAIL SAVE ERROR] {str(inner)}")
                return None

    # =====================================================
    # STATUS UPDATE NOTIFICATION
    # =====================================================
    @staticmethod
    def send_status_update(
        db: Session,
        user_id: int,
        application_id: int,
        status: str
    ):
        data = {
            "user_id": user_id,
            "application_id": application_id,
            "title": "Loan Application Status Updated",
            "message": f"Your loan application status is now: {status}",
            "type": "STATUS_UPDATE",
            "channel": "IN_APP",
            "status": "SENT"
        }

        if settings.USE_MOCK_DATA:
            logger.info("[MOCK NOTIFICATION] Status update")
            return NotificationRepository.create(db, data)

        return NotificationService._create_notification(db, data)

    # =====================================================
    # CUSTOM MESSAGE NOTIFICATION
    # =====================================================
    @staticmethod
    def send_custom_message(
        db: Session,
        user_id: int,
        application_id: int,
        title: str,
        message: str,
        notif_type: str = "DOCUMENT",
        channel: str = "IN_APP"
    ):
        data = {
            "user_id": user_id,
            "application_id": application_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "channel": channel,
            "status": "SENT"
        }

        if settings.USE_MOCK_DATA:
            logger.info("[MOCK NOTIFICATION] Custom message")
            return NotificationRepository.create(db, data)

        return NotificationService._create_notification(db, data)

    # =====================================================
    # GET USER NOTIFICATIONS
    # =====================================================
    @staticmethod
    def get_user_notifications(db: Session, user_id: int):
        return NotificationRepository.get_user_notifications(db, user_id)

    # =====================================================
    # MARK AS READ
    # =====================================================
    @staticmethod
    def mark_as_read(db: Session, notification_id: int):
        try:
            return NotificationRepository.mark_as_read(db, notification_id)
        except Exception as e:
            logger.error(f"[MARK READ ERROR] {str(e)}")
            return None