import uuid
import random

otp_store = {}

class MockESignProvider:

    async def initiate_esign(self, payload: dict):

        transaction_id = uuid.uuid4().hex
        otp = str(random.randint(100000, 999999))

        otp_store[transaction_id] = otp

        print(f"TEST OTP: {otp}")   # ← This prints OTP in terminal

        return {
            "transaction_id": transaction_id,
            "status": "OTP_SENT",
            "masked_aadhaar": "XXXXXXXX1234",
            "message": "OTP sent successfully"
        }

    async def verify_esign(self, payload: dict):

        txn = payload["transaction_id"]
        otp = payload["otp"]

        if otp_store.get(txn) != otp:
            return {"status": "FAILED", "message": "Invalid OTP"}

        return {
            "transaction_id": txn,
            "status": "SIGNED",
            "signed_pdf_url": "LOCAL"
        }