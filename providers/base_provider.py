class BaseESignProvider:

    async def initiate_esign(self, payload: dict):
        raise NotImplementedError("initiate_esign must be implemented")

    async def verify_esign(self, payload: dict):
        raise NotImplementedError("verify_esign must be implemented")

    async def verify_callback(self, payload: dict, headers: dict):
        raise NotImplementedError("verify_callback must be implemented")

    async def download_signed_pdf(self, url: str):
        raise NotImplementedError("download_signed_pdf must be implemented")