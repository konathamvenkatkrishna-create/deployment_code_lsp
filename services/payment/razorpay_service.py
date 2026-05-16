import requests
from requests.auth import HTTPBasicAuth

from core.config import settings
from core.logger import logger


class RazorpayService:

    BASE_URL = "https://api.razorpay.com/v1"

    def process_payout(
        self,
        name: str,
        account_number: str,
        ifsc: str,
        amount: float,
        email: str,
        phone: str
    ):

        # =====================================================
        # 🧪 MOCK MODE
        # =====================================================
        if settings.USE_MOCK_PAYOUT:

            logger.info("[MOCK PAYOUT] Running in test mode")

            return {
                "success": True,
                "payout_id": f"mock_payout_{phone}",
                "status": "processing"
            }

        # =====================================================
        # 🔴 VALIDATE KEYS
        # =====================================================
        if (
            not settings.RAZORPAYX_KEY_ID
            or not settings.RAZORPAYX_KEY_SECRET
            or not settings.RAZORPAYX_ACCOUNT_NUMBER
        ):
            return {
                "success": False,
                "error": "RazorpayX credentials missing"
            }

        try:

            # =====================================================
            # STEP 1: CREATE CONTACT
            # =====================================================
            contact_payload = {
                "name": name,
                "email": email,
                "contact": phone,
                "type": "customer"
            }

            contact_response = requests.post(
                f"{self.BASE_URL}/contacts",
                json=contact_payload,
                auth=HTTPBasicAuth(
                    settings.RAZORPAYX_KEY_ID,
                    settings.RAZORPAYX_KEY_SECRET
                )
            )

            if contact_response.status_code not in [200, 201]:

                logger.error(contact_response.text)

                return {
                    "success": False,
                    "error": "Failed to create contact"
                }

            contact_id = contact_response.json()["id"]

            # =====================================================
            # STEP 2: CREATE FUND ACCOUNT
            # =====================================================
            fund_account_payload = {
                "contact_id": contact_id,
                "account_type": "bank_account",
                "bank_account": {
                    "name": name,
                    "ifsc": ifsc,
                    "account_number": account_number
                }
            }

            fund_response = requests.post(
                f"{self.BASE_URL}/fund_accounts",
                json=fund_account_payload,
                auth=HTTPBasicAuth(
                    settings.RAZORPAYX_KEY_ID,
                    settings.RAZORPAYX_KEY_SECRET
                )
            )

            if fund_response.status_code not in [200, 201]:

                logger.error(fund_response.text)

                return {
                    "success": False,
                    "error": "Failed to create fund account"
                }

            fund_account_id = fund_response.json()["id"]

            # =====================================================
            # STEP 3: CREATE PAYOUT
            # =====================================================
            payout_payload = {
                "account_number": settings.RAZORPAYX_ACCOUNT_NUMBER,
                "fund_account_id": fund_account_id,
                "amount": int(amount * 100),
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": f"loan_{phone}"
            }

            payout_response = requests.post(
                f"{self.BASE_URL}/payouts",
                json=payout_payload,
                auth=HTTPBasicAuth(
                    settings.RAZORPAYX_KEY_ID,
                    settings.RAZORPAYX_KEY_SECRET
                )
            )

            if payout_response.status_code not in [200, 201]:

                logger.error(payout_response.text)

                return {
                    "success": False,
                    "error": "Payout failed"
                }

            payout_data = payout_response.json()

            logger.info(
                f"[PAYOUT CREATED] payout_id={payout_data.get('id')}"
            )

            return {
                "success": True,
                "payout_id": payout_data.get("id"),
                "status": payout_data.get("status", "processing")
            }

        except Exception as e:

            logger.error(f"[RAZORPAY ERROR] {str(e)}")

            return {
                "success": False,
                "error": str(e)
            }