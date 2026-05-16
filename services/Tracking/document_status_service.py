from sqlalchemy.orm import Session

from core.logger import logger
from core.enums import LoanApplicationStatus

from repositories.Tracking.kyc_reader_repo import KYCReaderRepository


class DocumentStatusService:

    @staticmethod
    def get_document_status(db: Session, application):
        """
        Prepare document-level response for UI
        """

        docs = KYCReaderRepository.get_user_documents(
            db,
            application.user_profile_id
        )

        if not docs:
            logger.warning(f"[KYC] No documents found for application_id={application.id}")

        response = []
        has_rejection = False

        for doc in docs:

            status_value = doc.status.value if doc.status else None

            item = {
                "document_type": doc.document_type.value if doc.document_type else None,
                "status": status_value,
                "reason": doc.admin_remarks,
                "action": None
            }

            # 🔥 Highlight rejected docs
            if status_value == "REJECTED":
                item["action"] = "REUPLOAD_REQUIRED"
                has_rejection = True

                logger.info(
                    f"[KYC REJECTED] app_id={application.id}, doc={item['document_type']}"
                )

            response.append(item)

        # 🔥 Application status override (SAFE)
        if has_rejection:
            application_status = LoanApplicationStatus.VERIFICATION_PENDING.value
        else:
            application_status = (
                application.application_status.value
                if application.application_status
                else None
            )

        return {
            "application_id": application.id,
            "application_status": application_status,
            "documents": response
        }