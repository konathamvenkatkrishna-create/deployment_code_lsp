from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from models.Tracking.notification import Notification


class NotificationRepository:

    @staticmethod
    def create(db: Session, data: dict):
        notif = Notification(**data)
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def get_user_notifications(db: Session, user_id: int):
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, notification_id: int):
        return db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int):
        notif = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notif:
            return None

        notif.is_read = True
        notif.read_at = func.now()
        db.commit()
        db.refresh(notif)
        return notif