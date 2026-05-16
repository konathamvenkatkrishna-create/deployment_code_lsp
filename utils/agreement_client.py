import requests
from core.config import settings

def initiate_esign(application_id, user_id):
    url = f"{settings.MODULE_7_URL}/api/v1/loan/esign/initiate"

    payload = {
        "application_id": application_id,
        "user_id": user_id
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"eSign initiation failed: {response.text}")

    return response.json()