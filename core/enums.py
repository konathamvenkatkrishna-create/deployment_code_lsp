from enum import Enum, IntEnum


def enum_value(value):
    """
    Safely convert Enum → string for DB / JSON
    """
    if isinstance(value, Enum):
        return value.value
    return value


# =====================================================
# CREDIT / BUREAU
# =====================================================
class CreditProvider(str, Enum):
    SUREPASS = "SUREPASS"
    KARZA = "KARZA"
    FINBOX = "FINBOX"


class InquiryType(str, Enum):
    SOFT = "SOFT"
    HARD = "HARD"


# =====================================================
# LOAN APPLICATION
# =====================================================
class LoanPurpose(str, Enum):
    MEDICAL = "MEDICAL"
    EDUCATION = "EDUCATION"
    EMERGENCY = "EMERGENCY"
    PERSONAL = "PERSONAL"


class LoanApplicationStep(str, Enum):
    EMI_CALCULATED = "EMI_CALCULATED"
    PURPOSE = "PURPOSE"
    REFERENCES = "REFERENCES"
    DECLARATION = "DECLARATION"
    SUMMARY = "SUMMARY"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"


class LoanApplicationStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    AGREEMENT_GENERATED = "AGREEMENT_GENERATED"
    ESIGN_COMPLETED = "ESIGN_COMPLETED"
    NBFC_APPROVED = "NBFC_APPROVED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DISBURSEMENT_INITIATED = "DISBURSEMENT_INITIATED"
    REJECTED = "REJECTED"


# =====================================================
# ELIGIBILITY
# =====================================================
class EligibilityStatusEnum(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED = "REJECTED"


class LoanTenureMonths(IntEnum):
    THREE = 3
    SIX = 6
    NINE = 9
    TWELVE = 12


# =====================================================
# REFERENCES
# =====================================================
class ReferenceRelation(str, Enum):
    FRIEND = "FRIEND"
    BROTHER = "BROTHER"
    SISTER = "SISTER"
    FATHER = "FATHER"
    MOTHER = "MOTHER"
    SPOUSE = "SPOUSE"
    COLLEAGUE = "COLLEAGUE"


# =====================================================
# DISBURSEMENT / PAYMENT
# =====================================================
class DisbursementStatusEnum(str, Enum):
    PENDING = "PENDING"
    INITIATED = "INITIATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class PaymentModeEnum(str, Enum):
    BANK = "BANK"
    UPI = "UPI"


# =====================================================
# SUPPORT / COMPLAINTS
# =====================================================
class ComplaintCategory(str, Enum):
    LOGIN_ISSUE = "Login Issue"
    KYC_ISSUE = "KYC Issue"
    PAYMENT_ISSUE = "Payment Issue"
    LOAN_ISSUE = "Loan Issue"
    TECHNICAL_ISSUE = "Technical Issue"
    ACCOUNT_ISSUE = "Account Issue"
    GENERAL_INQUIRY = "General Inquiry"
    FEEDBACK = "Feedback"
    OTHER = "Other"


class ComplaintPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ComplaintStatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


# =====================================================
# ADMIN
# =====================================================
class AdminCreateRole(str, Enum):
    LENDER = "LENDER"
    SUPPORT = "SUPPORT"