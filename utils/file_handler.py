from pathlib import Path
import hashlib
import httpx
from urllib.parse import urlparse
from datetime import datetime

from core.config import settings
from core.logger import logger


class FileHandler:
    """
    Handles saving signed PDFs securely.
    Provides both async + sync support.
    """

    def __init__(self):
        self.signed_dir: Path = Path(settings.SIGNED_PDF_PATH)
        self.signed_dir.mkdir(parents=True, exist_ok=True)

    # ASYNC SAVE FOR SIGNED PDF (USED IN EsignService)
    def _build_filename(self, txn_id: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return self.signed_dir / f"signed_{txn_id}_{timestamp}.pdf"

    async def save_signed_pdf_async(self, content: bytes, txn: str):
        """
        Saves provider-signed PDF content to disk asynchronously.
        """
        file_path: Path = self._build_filename(txn)

        logger.info(f"[FILE] Saving signed PDF -> {file_path}")

        # Write content
        try:
            file_path.write_bytes(content)
        except Exception as exc:
            logger.error(f"[FILE] Failed to write PDF: {exc}")
            raise ValueError("Failed to save signed PDF")

        # Generate hash
        file_hash = self.generate_sha256(file_path)
        return str(file_path), file_hash

    # SECURE DOWNLOAD (ASYNC)
    async def download_and_save_pdf_async(self, url: str, txn: str):
        """
        Secure PDF download + save + hash.
        """

        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid PDF URL")

        file_path: Path = self._build_filename(txn)
        logger.info(f"[FILE] Downloading PDF -> {url}")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)

            if resp.status_code != 200:
                raise ValueError("Failed to download PDF")

            content_type = resp.headers.get("Content-Type", "").lower()
            if "pdf" not in content_type:
                logger.warning(f"[FILE] Unexpected content-type: {content_type}")

            content = resp.content

        # Validate file size (max 10MB)
        if len(content) > 10 * 1024 * 1024:
            raise ValueError("PDF size too large")

        file_path.write_bytes(content)

        file_hash = self.generate_sha256(file_path)
        return str(file_path), file_hash

    # HASH GENERATION
    def generate_sha256(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()

        try:
            with file_path.open("rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
        except Exception as exc:
            logger.error(f"[FILE] Hashing failed: {exc}")
            raise ValueError("Unable to hash file")

        return sha256.hexdigest()