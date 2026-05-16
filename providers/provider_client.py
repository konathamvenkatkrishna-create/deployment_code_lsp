import httpx
from core.config import settings
from core.exceptions import throw_error
from core.logger import logger


class ProviderClient:
    """
    Low-level HTTP client for eSign providers.
    Handles retries, timeouts, headers, and response validation.
    """

    def __init__(self):
        self.base_url = settings.ESIGN_BASE_URL.rstrip("/")

        self.timeout = httpx.Timeout(
            connect=3.0,
            read=10.0,
            write=5.0,
            pool=5.0,
        )

        self.retry_statuses = {502, 503, 504}

    def _headers(self):
        return {
            "X-API-Key": settings.ESIGN_API_KEY,
            "X-Client-Secret": settings.ESIGN_CLIENT_SECRET,
            "Content-Type": "application/json",
        }

    # PUBLIC METHODS

    async def post(self, path: str, payload: dict):
        return await self._post(path, payload)

    async def get(self, path: str):
        return await self._get(path)

    # INTERNAL METHODS

    async def _post(self, path: str, payload: dict):
        url = f"{self.base_url}/{path.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(2):
                try:
                    logger.info(f"[Provider POST] {url}")

                    resp = await client.post(
                        url,
                        json=payload,
                        headers=self._headers()
                    )

                except httpx.ConnectError:
                    if attempt == 0:
                        continue
                    throw_error("eSign provider unreachable", 503)

                if resp.status_code in self.retry_statuses and attempt == 0:
                    continue

                break

        if resp.status_code != 200:
            logger.error(f"[Provider POST ERROR] status={resp.status_code}, url={url}")
            throw_error("Provider API error", 503)

        try:
            return resp.json()
        except Exception:
            throw_error("Invalid JSON from provider", 502)

    async def _get(self, path: str):
        url = f"{self.base_url}/{path.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(2):
                try:
                    logger.info(f"[Provider GET] {url}")

                    resp = await client.get(
                        url,
                        headers=self._headers()
                    )

                except httpx.ConnectError:
                    if attempt == 0:
                        continue
                    throw_error("Provider unreachable", 503)

                if resp.status_code in self.retry_statuses and attempt == 0:
                    continue

                break

        if resp.status_code != 200:
            logger.error(f"[Provider GET ERROR] status={resp.status_code}, url={url}")
            throw_error("Provider fetch failed", 503)

        try:
            return resp.json()
        except Exception:
            throw_error("Invalid JSON from provider", 502)