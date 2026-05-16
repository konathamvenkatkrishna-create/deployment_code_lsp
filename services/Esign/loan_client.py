import httpx

from core.config import settings
from core.exceptions import throw_error


class LoanClient:

    def __init__(self):
        self.base_url = settings.LOAN_SERVICE_BASE_URL.rstrip("/")

    def get_loan_sync(self, loan_id: int):

        url = f"{self.base_url}/{loan_id}"

        try:
            resp = httpx.get(url, timeout=5)

        except httpx.ConnectError:
            throw_error("Loan service unreachable", 503)

        if resp.status_code == 404:
            throw_error("Loan not found", 404)

        if resp.status_code != 200:
            throw_error("Loan service error", 503)

        try:
            data = resp.json()
        except Exception:
            throw_error("Invalid loan service response", 502)

        return data.get("data")