import requests
from core.config import settings


def generate_emi(token: str):
    url = f"{settings.MODULE_8_URL}/emis/generate"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"EMI generation failed: {response.text}")

    return response.json()