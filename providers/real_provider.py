from providers.base_provider import BaseESignProvider
from providers.provider_client import ProviderClient
import uuid


class RealESignProvider(BaseESignProvider):
    """
    Real provider implementation.
    This class maps our internal eSign operations
    to the external provider API endpoints.
    """

    def __init__(self):
        self.client = ProviderClient()

    # Initiate eSign (Send OTP)
    async def initiate_esign(self, payload: dict):

        resp = await self.client._post("post", payload)

    # simulate provider response
        return {
            "transaction_id": str(uuid.uuid4()) ,
            "status": "OTP_SENT",
            "masked_aadhaar": "XXXXXXXX1234",
            "message": "OTP sent successfully"
        }

    # Verify OTP and sign document
    async def initiate_esign(self, payload: dict):

        resp = await self.client._post("post", payload)

        # simulate provider response
        return {
            "transaction_id": str(uuid.uuid4()),
            "status": "OTP_SENT",
            "masked_aadhaar": "XXXXXXXX1234",
            "message": "OTP sent successfully"
        }

    # Fetch agreement details from provider
    async def fetch_agreement(self, loan_id: int):
        return await self.client._get(f"get")