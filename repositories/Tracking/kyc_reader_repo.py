# repositories/kyc_reader_repo.py (Module 6)

from sqlalchemy.orm import Session
from models.Profile_KYC.document_upload import DocumentUpload


class KYCReaderRepository:

    @staticmethod
    def get_user_documents(db: Session, user_id: int):
        return db.query(DocumentUpload).filter(
            DocumentUpload.user_id == user_id
        ).all()