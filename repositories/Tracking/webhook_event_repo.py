from sqlalchemy.orm import Session
from models.Tracking.webhook_event import WebhookEvent


class WebhookEventRepository:

    @staticmethod
    def exists(db: Session, event_id: str):
        return (
            db.query(WebhookEvent)
            .filter(WebhookEvent.event_id == event_id)
            .first()
        )

    @staticmethod
    def create(db: Session, data: dict):
        event = WebhookEvent(**data)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def mark_processed(db: Session, event_id: str):
        event = WebhookEventRepository.exists(db, event_id)
        if not event:
            return None

        event.status = "PROCESSED"
        db.commit()
        db.refresh(event)
        return event

    # ✅ NEW METHOD ADDED
    @staticmethod
    def mark_failed(db: Session, event_id: str):
        event = WebhookEventRepository.exists(db, event_id)
        if not event:
            return None

        event.status = "FAILED"
        db.commit()
        db.refresh(event)
        return event