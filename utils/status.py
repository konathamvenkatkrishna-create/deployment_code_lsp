import requests
 
def close_loan(application_id, user_id):
    url = "http://localhost:8000/internal/status/update"
 
    payload = {
        "application_id": application_id,
        "user_id": user_id,
        "status": "CLOSED",
        "comment": "All EMIs paid successfully"
    }
 
    response = requests.post(url, json=payload)
 
    if response.status_code != 200:
        raise Exception(f"Failed to close loan: {response.text}")
 
    return response.json()