from sqlalchemy.orm import Session
from models.Profile_KYC.document_upload import DocumentUpload, DocumentType, DocumentStatus
from typing import List, Optional
from datetime import datetime

class DocumentUploadRepository:

    @staticmethod
    def get_by_id(db: Session, document_id: int) -> Optional[DocumentUpload]:
        return db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> List[DocumentUpload]:
        return db.query(DocumentUpload).filter(DocumentUpload.user_id == user_id).all()

    @staticmethod
    def get_by_email(db: Session, email: str) -> List[DocumentUpload]:
        return db.query(DocumentUpload).filter(DocumentUpload.email == email).all()

    @staticmethod
    def get_by_user_and_type(db: Session, user_id: int, document_type: DocumentType) -> Optional[DocumentUpload]:
        return (
            db.query(DocumentUpload)
            .filter( DocumentUpload.user_id == user_id,DocumentUpload.document_type == document_type,).first()
        )

    @staticmethod
    def create_document(db: Session, document: DocumentUpload) -> DocumentUpload:
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def update_document(db: Session, document: DocumentUpload) -> DocumentUpload:
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def delete_document(db: Session, document: DocumentUpload) -> None:
        db.delete(document)
        db.commit()

    @staticmethod
    def count_all(db: Session) -> int:
        return db.query(DocumentUpload).count()

    @staticmethod
    def count_by_status(db: Session, status: DocumentStatus) -> int:
        return db.query(DocumentUpload).filter(DocumentUpload.status == status).count()

    @staticmethod
    def get_pending_documents(db: Session) -> List[DocumentUpload]:
        return (
            db.query(DocumentUpload).filter(DocumentUpload.status == DocumentStatus.UPLOADED).all())

    @staticmethod
    def get_rejected_documents_before_date(db: Session, cutoff_date: datetime) -> List[DocumentUpload]:
        return (
            db.query(DocumentUpload)
            .filter(DocumentUpload.status == DocumentStatus.REJECTED, DocumentUpload.reviewed_at <  cutoff_date,).all()
        )

    @staticmethod
    def get_by_user_and_status(db: Session, user_id: int, status: DocumentStatus) -> List[DocumentUpload]:
        return (
            db.query(DocumentUpload)
            .filter( DocumentUpload.user_id == user_id, DocumentUpload.status  == status,).all()
        )