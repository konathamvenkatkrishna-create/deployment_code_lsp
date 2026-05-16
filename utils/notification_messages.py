from enum import Enum


# =========================
# APPLICATION STATUS ENUM
# =========================
class ApplicationStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    CREDIT_CHECK = "CREDIT_CHECK"
    LENDER_REVIEW = "LENDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AGREEMENT_PENDING = "AGREEMENT_PENDING"
    DISBURSEMENT_INITIATED = "DISBURSEMENT_INITIATED"
    DISBURSED = "DISBURSED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


# =========================
# NOTIFICATION MESSAGES ENUM
# =========================
class NotificationMessages(str, Enum):
    STATUS_UPDATED = "Your loan application status has been updated."

    APPLICATION_SUBMITTED = "Your loan application has been submitted successfully."
    APPLICATION_UNDER_REVIEW = "Your application is under review."
    APPLICATION_APPROVED = "Congratulations! Your loan application has been approved."
    APPLICATION_REJECTED = "Unfortunately, your loan application was rejected."

    CREDIT_CHECK_STARTED = "Your credit check is currently in progress."

    AGREEMENT_PENDING = "Your loan agreement is pending e-sign."

    DISBURSEMENT_INITIATED = "Your loan disbursement has been initiated."
    LOAN_DISBURSED = "Your loan amount has been successfully credited to your account."

    LOAN_ACTIVE = "Your loan is now active."
    LOAN_CLOSED = "Your loan has been closed. Thank you for choosing us!"

    DOCUMENT_REUPLOAD_REQUIRED = "Additional documents are required. Please reupload the requested document."
    DOCUMENT_REUPLOAD_SUBMITTED = "Your document has been successfully reuploaded and is under review."

    NBFC_STATUS_UPDATE = "Your loan status has been updated by the lending partner."


# =========================
# STATUS → MESSAGE MAPPING FUNCTION
# =========================
def get_notification_message(status: str) -> str:
    mapping = {
        ApplicationStatus.SUBMITTED: NotificationMessages.APPLICATION_SUBMITTED,
        ApplicationStatus.UNDER_REVIEW: NotificationMessages.APPLICATION_UNDER_REVIEW,
        ApplicationStatus.VERIFICATION_PENDING: NotificationMessages.DOCUMENT_REUPLOAD_REQUIRED,
        ApplicationStatus.CREDIT_CHECK: NotificationMessages.CREDIT_CHECK_STARTED,
        ApplicationStatus.LENDER_REVIEW: NotificationMessages.APPLICATION_UNDER_REVIEW,
        ApplicationStatus.APPROVED: NotificationMessages.APPLICATION_APPROVED,
        ApplicationStatus.REJECTED: NotificationMessages.APPLICATION_REJECTED,
        ApplicationStatus.AGREEMENT_PENDING: NotificationMessages.AGREEMENT_PENDING,
        ApplicationStatus.DISBURSEMENT_INITIATED: NotificationMessages.DISBURSEMENT_INITIATED,
        ApplicationStatus.DISBURSED: NotificationMessages.LOAN_DISBURSED,
        ApplicationStatus.ACTIVE: NotificationMessages.LOAN_ACTIVE,
        ApplicationStatus.CLOSED: NotificationMessages.LOAN_CLOSED,
    }

    return mapping.get(status, NotificationMessages.STATUS_UPDATED).value