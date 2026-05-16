from functools import lru_cache
from pathlib import Path
from typing import List, Optional
 
from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
 
    # ============================================================
    # ENVIRONMENT
    # ============================================================
    APP_ENV: str = "development"
    ENV: str = "dev"
    DEFAULT_CONSENT_VERSION: str = "v1.0"
 
    # ============================================================
    # DATABASE
    # ============================================================
    DATABASE_URL: str
 
    # ============================================================
    # SECURITY
    # ============================================================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
 
    # ============================================================
    # REDIS (OTP / CACHE)
    # ============================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
 
    # ============================================================
    # SMS CONFIG (MSG91)
    # ============================================================
    MSG91_API_KEY: Optional[str] = None
    MSG91_FLOW_ID: Optional[str] = None
    MSG91_SENDER_ID: str = "MSGIND"
    COUNTRY_CODE: str = "91"
 
    SMS_ENABLED: bool = False
 
    # ============================================================
    # TWILIO (OPTIONAL)
    # ============================================================
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
 
    # ============================================================
    # MAIL CONFIG
    # ============================================================
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
 
    # ============================================================
    # SUPER ADMIN
    # ============================================================
    SUPERADMIN_TOKEN: Optional[str] = None
    SUPER_ADMIN_NAME: Optional[str] = None
    SUPER_ADMIN_MOBILE: Optional[str] = None
    SUPER_ADMIN_DEVICE_ID: Optional[str] = None
    SUPER_ADMIN_PASSWORD: Optional[str] = None
 
    # ============================================================
    # KYC LIMITS
    # ============================================================
    PAN_MAX_ATTEMPTS: int = 3
    AADHAAR_MAX_ATTEMPTS: int = 3
    BANK_MAX_ATTEMPTS: int = 3
 
    PAN_COOLDOWN_HOURS: int = 24
    AADHAAR_COOLDOWN_HOURS: int = 24
    BANK_COOLDOWN_HOURS: int = 24
 
    NAME_MATCH_THRESHOLD: float = 80.0
 
    # ============================================================
    # FILE UPLOAD
    # ============================================================
    MAX_FILE_SIZE_MB: int = 2
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]
    ALLOWED_DOCUMENT_EXTENSIONS: List[str] = [".pdf"]
 
    # ============================================================
    # DATA RETENTION
    # ============================================================
    RETENTION_DAYS: int = 90
    TRACKER_CLEANUP_HOURS: int = 48
    REJECTED_DOCS_RETENTION_DAYS: int = 90
 
    # ============================================================
    # CLOUDINARY
    # ============================================================
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
 
    # ============================================================
    # DIGILOCKER
    # ============================================================
    DIGILOCKER_CLIENT_ID: Optional[str] = None
    DIGILOCKER_CLIENT_SECRET: Optional[str] = None
    DIGILOCKER_REDIRECT_URI: Optional[str] = None
 

# ============================================================
# PAYMENT (RAZORPAY / RAZORPAYX)
# ============================================================

    # Razorpay (Payments)
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    # RazorpayX (Payouts)
    RAZORPAYX_KEY_ID: Optional[str] = None
    RAZORPAYX_KEY_SECRET: Optional[str] = None
    RAZORPAYX_ACCOUNT_NUMBER: Optional[str] = None

    # Base URL
    RAZORPAY_BASE_URL: str = "https://api.razorpay.com/v1"

    # Webhooks
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAYX_WEBHOOK_SECRET: str = ""

    # Mode / Testing
    RAZORPAY_MODE: str = "test"
    USE_MOCK_PAYOUT: bool = True     #   change to False to enable real RazorpayX integration
 
    # ============================================================
    # ESIGN
    # ============================================================
    AGREEMENT_STORAGE_PATH: str = "storage/generated_pdfs"
    SIGNED_PDF_PATH: str = "storage/signed_pdfs"
 
    ESIGN_PROVIDER: str = "eMudhra"
 
    LOAN_SERVICE_BASE_URL: str = "http://localhost:8000/api/v1/loans"
 
    # ============================================================
    # MODULE INTEGRATION
    # ============================================================
    MODULE_7_URL: Optional[str] = "http://localhost:8001"
    MODULE_8_URL: Optional[str] = "http://localhost:8002"
 
    # ============================================================
    # COMPUTED
    # ============================================================
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
 
    # ============================================================
    # PYDANTIC CONFIG
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        case_sensitive=True,
        extra="ignore",
    )
 
 
@lru_cache
def get_settings() -> Settings:
    return Settings()
 
 
settings = get_settings()
 