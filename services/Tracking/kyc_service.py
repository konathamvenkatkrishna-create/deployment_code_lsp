# services/document_status_service.py

from repositories.Tracking.kyc_reader_repo import KYCReaderRepository

class DocumentStatusService:

    @staticmethod
    def get_document_status(db, application):

        docs = KYCReaderRepository.get_user_documents(
            db,
            application.user_profile_id
        )

        response = []

        has_rejection = False

        for doc in docs:

            item = {
                "document_type": doc.document_type.value,
                "status": doc.status.value,
                "reason": doc.admin_remarks,
                "action": None
            }

            if doc.status.value == "REJECTED":
                item["action"] = "REUPLOAD_REQUIRED"
                has_rejection = True

            response.append(item)

        # decide application status
        if has_rejection:
            application_status = "VERIFICATION_PENDING"
        else:
            application_status = application.application_status

        return {
            "application_id": application.id,
            "application_status": application_status,
            "documents": response
        }
