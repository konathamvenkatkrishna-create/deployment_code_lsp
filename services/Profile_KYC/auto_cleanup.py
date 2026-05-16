import threading
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_
from core.database import SessionLocal
from models.Profile_KYC.attempt_tracker import AttemptTracker
from models.Profile_KYC.document_upload import DocumentStatus
from repositories.Profile_KYC.document_upload_repository import DocumentUploadRepository
from repositories.Profile_KYC.kyc_pan_verification_repository import KYCPANVerificationRepository
from repositories.Profile_KYC.kyc_aadhaar_verification_repository import KYCAadhaarVerificationRepository
from repositories.Profile_KYC.kyc_bank_verification_repository import KYCBankVerificationRepository
from core.config import settings
import cloudinary.uploader

def _extract_cloudinary_public_id(url: str):
    try:
        marker = "/upload/"
        idx = url.find(marker)
        if idx == -1:
            return None

        after_upload = url[idx + len(marker):]   # "v1234567890/kyc/1/PAN_CARD/document.jpg"

        # Strip optional version segment (v followed by only digits)
        if after_upload.startswith("v") and "/" in after_upload:
            potential_version = after_upload[1 : after_upload.index("/")]
            if potential_version.isdigit():
                after_upload = after_upload[after_upload.index("/") + 1:]

        # Strip file extension from the last path component
        if "." in after_upload.split("/")[-1]:
            after_upload = after_upload.rsplit(".", 1)[0]

        return after_upload  # e.g. "kyc/1/PAN_CARD/document"
    except Exception:
        return None


def _delete_cloudinary_asset(url: str) -> None:
    """Best-effort Cloudinary delete; never raises."""
    public_id = _extract_cloudinary_public_id(url)
    if not public_id:
        print(f"Could not extract public_id from URL: {url}")
        return
    try:
        # Attempt both resource types — Cloudinary silently ignores the wrong one
        cloudinary.uploader.destroy(public_id, resource_type="image")
        cloudinary.uploader.destroy(public_id, resource_type="raw")
        print(f"Deleted Cloudinary asset: {public_id}")
    except Exception as e:
        print(f"Cloudinary delete failed for {public_id}: {e}")


class AutoCleanup:

    def __init__(self, interval_hours: int = 24):
        self.interval_hours = interval_hours
        self._running       = False
        self._thread        = None
        print(f"AutoCleanup initialized with interval: {interval_hours}h")

    def start(self):
        if self._running:
            print("Auto cleanup already running")
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"Auto cleanup started (runs every {self.interval_hours}h)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("Auto cleanup stopped")

    def is_running(self):
        return self._running

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------
    def _run(self):
        while self._running:
            try:
                self._cleanup()
            except Exception as e:
                print(f"Cleanup error: {str(e)}")
            time.sleep(self.interval_hours * 3600)

    def _cleanup(self):
        db = SessionLocal()
        try:
            print("Starting cleanup...")

            expired_trackers     = self._cleanup_expired_trackers(db)
            failed_verifications = self._cleanup_failed_verifications(db)
            rejected_docs        = self._cleanup_rejected_documents(db)

            print(
                f"Cleanup completed: "
                f"{expired_trackers} trackers, "
                f"{failed_verifications} verifications, "
                f"{rejected_docs} documents removed"
            )
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 1. Expired / useless attempt trackers
    # ------------------------------------------------------------------
    def _cleanup_expired_trackers(self, db) -> int:
        try:
            now    = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=settings.TRACKER_CLEANUP_HOURS)

            old_trackers = db.query(AttemptTracker).filter(
                and_(
                    AttemptTracker.locked_until.isnot(None),
                    AttemptTracker.locked_until < cutoff,
                )
            ).all()

            useless_trackers = db.query(AttemptTracker).filter(
                and_(
                    AttemptTracker.locked_until.is_(None),
                    AttemptTracker.attempts_count == 0,
                )
            ).all()

            total = len(old_trackers) + len(useless_trackers)

            for t in old_trackers:
                print(
                    f"Deleting old tracker: {t.email}, "
                    f"type: {t.verification_type}, "
                    f"locked_until: {t.locked_until}"
                )
                db.delete(t)

            for t in useless_trackers:
                print(
                    f"Deleting useless tracker: {t.email}, "
                    f"type: {t.verification_type}, "
                    f"attempts=0, locked_until=null"
                )
                db.delete(t)

            if total > 0:
                db.commit()
                print(
                    f"Deleted {total} trackers "
                    f"(old: {len(old_trackers)}, useless: {len(useless_trackers)})"
                )

            return total

        except Exception as e:
            db.rollback()
            print(f"Tracker cleanup error: {str(e)}")
            return 0

    # ------------------------------------------------------------------
    # 2. Old failed verifications
    # ------------------------------------------------------------------
    def _cleanup_failed_verifications(self, db) -> int:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)

            pan_deleted     = KYCPANVerificationRepository.delete_failed_verifications(db, cutoff)
            aadhaar_deleted = KYCAadhaarVerificationRepository.delete_failed_verifications(db, cutoff)
            bank_deleted    = KYCBankVerificationRepository.delete_failed_verifications(db, cutoff)

            total = pan_deleted + aadhaar_deleted + bank_deleted

            if total > 0:
                db.commit()
                print(
                    f"Deleted {total} failed verifications "
                    f"(PAN: {pan_deleted}, Aadhaar: {aadhaar_deleted}, Bank: {bank_deleted}) "
                    f"older than {settings.RETENTION_DAYS} days"
                )

            return total

        except Exception as e:
            db.rollback()
            print(f"Verification cleanup error: {str(e)}")
            return 0

    # ------------------------------------------------------------------
    # 3. Rejected documents  (delete from Cloudinary, then from DB)
    # ------------------------------------------------------------------
    def _cleanup_rejected_documents(self, db) -> int:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=settings.REJECTED_DOCS_RETENTION_DAYS)

            rejected_docs = DocumentUploadRepository.get_rejected_documents_before_date(db, cutoff)
            count         = len(rejected_docs)

            for doc in rejected_docs:
                # file_path holds a Cloudinary URL — delete from Cloudinary, not local disk
                _delete_cloudinary_asset(doc.file_path)
                db.delete(doc)

            if count > 0:
                db.commit()
                print(
                    f"Deleted {count} rejected documents "
                    f"older than {settings.REJECTED_DOCS_RETENTION_DAYS} days"
                )

            return count

        except Exception as e:
            db.rollback()
            print(f"Document cleanup error: {str(e)}")
            return 0