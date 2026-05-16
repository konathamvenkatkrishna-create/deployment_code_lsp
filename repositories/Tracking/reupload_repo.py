from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.Tracking.document_reupload import DocumentReupload


class DocumentReuploadRepository:

    # -----------------------------------------
    # ✅ Create new document version
    # -----------------------------------------
    @staticmethod
    def create(db: Session, data: dict):
        doc = DocumentReupload(**data)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc


    # -----------------------------------------
    # ✅ Get latest document (highest version)
    # -----------------------------------------
    @staticmethod
    def get_latest(db: Session, application_id: int, document_type: str):
        return db.query(DocumentReupload).filter(
            DocumentReupload.application_id == application_id,
            DocumentReupload.document_type == document_type
        ).order_by(desc(DocumentReupload.version)).first()


    # -----------------------------------------
    # ✅ Check if last document is rejected
    # -----------------------------------------
    @staticmethod
    def get_last_rejected(db: Session, application_id: int, document_type: str):
        return db.query(DocumentReupload).filter(
            DocumentReupload.application_id == application_id,
            DocumentReupload.document_type == document_type,
            DocumentReupload.status == "REJECTED"
        ).order_by(desc(DocumentReupload.version)).first()


    # -----------------------------------------
    # ✅ Get all documents for an application
    # -----------------------------------------
    @staticmethod
    def get_all_by_application(db: Session, application_id: int):
        return db.query(DocumentReupload).filter(
            DocumentReupload.application_id == application_id
        ).order_by(desc(DocumentReupload.created_at)).all()


    # -----------------------------------------
    # ✅ Update document status (Module 2 will use)
    # -----------------------------------------
    @staticmethod
    def update_status(
        db: Session,
        document_id: int,
        status: str,
        rejection_reason: str = None
    ):
        doc = db.query(DocumentReupload).filter(
            DocumentReupload.id == document_id
        ).first()

        if not doc:
            return None

        doc.status = status

        if rejection_reason:
            doc.rejection_reason = rejection_reason

        db.commit()
        db.refresh(doc)

        return doc