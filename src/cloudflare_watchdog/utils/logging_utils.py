import logging
from datetime import datetime

logger = logging.getLogger("CloudflareWatchdog")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("watchdog.log", encoding="utf-8")
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    logger.info(message)
