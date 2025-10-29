import logging
import os
import requests
import subprocess
import sys
import time
import yaml
from datetime import datetime


def get_config_path():
    if getattr(sys, "frozen", False):  # PyInstaller bundle
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)

    path = os.path.join(base_path, "config.yaml")
    if not os.path.exists(path):
        fallback = os.path.join(os.getcwd(), "config.yaml")
        return fallback
    return path


CONFIG_PATH = get_config_path()
LOG_PATH = os.path.join(os.path.dirname(__file__), "watchdog.log")

# --- Rotating Log Setup ---
from logging.handlers import RotatingFileHandler

# --- Rotating Log Setup ---
from logging.handlers import RotatingFileHandler
from winotify import Notification

LOG_PATH = os.path.join(os.path.dirname(__file__), "watchdog.log")
logger = logging.getLogger("watchdog")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    LOG_PATH, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
)


class WatchdogCore:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.running = False
        self.load_config()

    def load_config(self):
        import yaml

        try:
            if not os.path.exists(self.config_path):
                default_cfg = {
                    "target_url": "https://example.com",
                    "check_interval": 30,
                    "retries": 3,
                }
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(default_cfg, f)
                self.config = default_cfg
            else:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
        except Exception as e:
            self.config = {}
            logger.error(f"Failed to load config: {e}")

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")
        logger.info(msg)
        try:
            toast = Notification(
                app_id="Cloudflare Watchdog", title="Cloudflare Watchdog", msg=msg
            )
            toast.show()
        except Exception:
            pass

    def start(self, log_callback=None):
        import time, requests

        self.running = True
        self.log("🔍 Starting watchdog monitor loop...")
        while self.running:
            try:
                self.load_config()
                url = self.config.get("target_url", "https://example.com")
                interval = int(self.config.get("check_interval", 30))
                retries = int(self.config.get("retries", 3))

                success = False
                for i in range(retries):
                    try:
                        r = requests.get(url, timeout=10)
                        if r.status_code == 200:
                            success = True
                            break
                    except Exception:
                        pass
                    time.sleep(2)

                if success:
                    msg = f"✅ Site online: {url}"
                else:
                    msg = f"⚠️ Site appears down after {retries} attempts: {url}"
                self.log(msg)
                if log_callback:
                    log_callback(msg)
                time.sleep(interval)

            except Exception as e:
                self.log(f"❌ Watchdog encountered error: {e}")
                time.sleep(5)

    def stop(self):
        self.running = False
        self.log("🛑 Watchdog stopped.")
