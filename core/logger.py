import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs folder
os.makedirs("logs", exist_ok=True)

LOG_FILE = "logs/app.log"

# Rotating log handler (5 MB max, keep 5 files)
handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

# Log format (PROD-READY)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

handler.setFormatter(formatter)

logger = logging.getLogger("E-Sign")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

