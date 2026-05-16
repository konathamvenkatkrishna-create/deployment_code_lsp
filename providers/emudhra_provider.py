from typing import Dict, Any
import json

from providers.base_provider import BaseESignProvider
from providers.provider_client import ProviderClient


class EmudhraProvider(BaseESignProvider):
    """
    Real eMudhra provider implementation.
    Handles mapping between eMudhra API and internal system format.
    """

    def __init__(self):
        self.client = ProviderClient()

    async def initiate_esign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.client.post("/esign/initiate", payload)

        return {
            "transaction_id": resp.get("txnId"),
            "masked_aadhaar": resp.get("maskedAadhaar"),
            "status": resp.get("status", "OTP_SENT"),
        }

    async def verify_esign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.client.post("/esign/verify", payload)

        return {
            "transaction_id": resp.get("txnId"),
            "status": resp.get("status"),
            "signed_pdf_url": resp.get("signedPdfUrl"),
        }

    async def verify_callback(self, raw_body: bytes) -> Dict[str, Any]:
        """
        Parse provider callback payload and convert it to internal format.
        """
        data = json.loads(raw_body)

        return {
            "transaction_id": data.get("txnId"),
            "status": data.get("status"),
            "signed_pdf_url": data.get("signedPdfUrl"),
        }

    async def download_signed_pdf(self, url: str) -> bytes:
        """
        Download signed PDF from provider.
        """
        return await self.client.get_file(url)