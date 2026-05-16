 
import os
import logging
from typing import Optional, Dict
import firebase_admin from firebase_admin import credentials

logger = logging.getLogger(__name__)
 
_firebase_app = None
 
 
def _init_firebase():
    global _firebase_app
 
    if _firebase_app:
        return _firebase_app
 
    
 
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase.json")
 
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Missing Firebase credentials at {cred_path}")
 
    cred = credentials.Certificate(cred_path)
    _firebase_app = firebase_admin.initialize_app(cred)
 
    logger.info("✅ Firebase initialized")
    return _firebase_app
 
 
# ── Stage Config ─────────────────────────────────────────
 
STAGE_CONFIG = {
    "PRE_DUE_7": {"priority": "normal", "channel": "emi_pre_due"},
    "PRE_DUE_3": {"priority": "high", "channel": "emi_pre_due"},
    "PRE_DUE_1": {"priority": "high", "channel": "emi_urgent"},
    "DUE_TODAY": {"priority": "high", "channel": "emi_urgent"},
    "OVERDUE": {"priority": "high", "channel": "emi_overdue"},
}
 
 
def _get_stage(stage: str):
    if stage.startswith("OVERDUE"):
        return STAGE_CONFIG["OVERDUE"]
    return STAGE_CONFIG.get(stage, STAGE_CONFIG["PRE_DUE_7"])
 
 
# ── Main Send Function ───────────────────────────────────
 
async def send_push(
    user,
    stage: str,
    body: str,
    data: Optional[Dict] = None,
) -> bool | str:
 
    if not user.fcm_token:
        return False
 
    if os.getenv("FCM_ENABLED", "true") != "true":
        logger.info(f"[FCM DISABLED] {body}")
        return True
 
    try:
        from firebase_admin import messaging
 
        _init_firebase()
 
        cfg = _get_stage(stage)
 
        message = messaging.Message(
            token=user.fcm_token,
 
            notification=messaging.Notification(
                title="EMI Reminder",
                body=body
            ),
 
            android=messaging.AndroidConfig(
                priority=cfg["priority"],
                notification=messaging.AndroidNotification(
                    channel_id=cfg["channel"],
                    click_action="FLUTTER_NOTIFICATION_CLICK",
                ),
            ),
 
            data={
                "stage": stage,
                **(data or {})
            }
        )
 
        response = messaging.send(message)
 
        logger.info(f"Push sent {response}")
        return True
 
    except Exception as e:
        err = str(e)
        logger.error(f"FCM Error: {err}")
 
        if "registration-token-not-registered" in err:
            return "INVALID_TOKEN"
 
        return False