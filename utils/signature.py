import hmac
import hashlib
from core.config import settings
from core.logger import logger


def verify_callback_signature(raw_body: bytes, signature: str) -> bool:
    """
    Secure HMAC verification for Aadhaar eSign Provider Callbacks.

    - Uses RAW request body, not Python dict
    - Stable JSON hashing (required by providers)
    - Constant-time comparison
    """

    try:
        secret = settings.ESIGN_CALLBACK_SECRET.encode("utf-8")

        # Provider always signs raw JSON body, not python dict
        expected = hmac.new(
            secret,
            raw_body,  # MUST BE RAW BODY
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected, signature)

        if not is_valid:
            logger.warning(
                f"Invalid callback signature: expected={expected}, received={signature}"
            )

        return is_valid

    except Exception as exc:
        logger.error(f"Signature verification error: {exc}", exc_info=True)
        return False