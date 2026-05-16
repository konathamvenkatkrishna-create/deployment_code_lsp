def success_response(message:str, data = None):
    return {
        "success":True,
        "message": message,
        "data": data
    }

def error_response(message: str, status_code:int = 400):
    return {
        "success":"ERROR",
        "message":message,
        "status": status_code
    }