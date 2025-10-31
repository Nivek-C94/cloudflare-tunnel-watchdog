import json
import logging
import os
import requests
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from winotify import Notification


def get_settings_path():
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home())) / "CloudflareWatchdog"
    else:
        base = Path.home() / ".config" / "cloudflare-watchdog"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


LOG_PATH = Path(__file__).parent / "watchdog.log"
logger = logging.getLogger("watchdog")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    LOG_PATH, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
)
logger.addHandler(handler)


class WatchdogCore:
    def __init__(self):
        self.settings_path = get_settings_path()
        self.running = False
        self.settings = self.load_settings()

    def load_settings(self):
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
        defaults = {
            "target_url": "https://example.com",
            "check_interval": 30,
            "retries": 3,
        }
        self.save_settings(defaults)
        return defaults

    def save_settings(self, data=None):
        data = data or self.settings
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

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
        self.running = True
        self.log("🔍 Starting watchdog monitor loop...")
        while self.running:
            try:
                self.settings = self.load_settings()
                url = self.settings.get("target_url", "https://example.com")
                interval = int(self.settings.get("check_interval", 30))
                retries = int(self.settings.get("retries", 3))

                msg = None  # Predefine message to avoid unbound errors
                success = False  # Predefine success flag
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        msg = f"✅ Site online: {url}"
                        success = True
                    else:
                        msg = f"⚠️ Unexpected status: {r.status_code}"
                except Exception as e:
                    self.log(f"❌ Watchdog encountered an error: {e}")
                    if msg:
                        self.log(msg)
                    else:
                        self.log(
                            "⚠️ No status message available — request failed before response."
                        )
                    msg = f"✅ Site online: {url}"
                    # --- Run On Recovery Commands ---
                    if self.settings.get("on_recovery"):
                        import subprocess

                        for command in self.settings.get("on_recovery", []):
                            self.log(f"🔁 Running on-recovery command: {command}")
                            try:
                                subprocess.run(command, shell=True, check=True)
                                self.log(f"✅ Command succeeded: {command}")
                                if log_callback:
                                    log_callback(f"✅ Command succeeded: {command}")
                            except subprocess.CalledProcessError as e:
                                self.log(f"❌ Command failed ({command}): {e}")
                                if log_callback:
                                    log_callback(f"❌ Command failed ({command}): {e}")

                    import subprocess

                    # Distinguish between site and Wi-Fi failures
                    if "requests.exceptions.ConnectionError" in str(locals()):
                        recovery_type = "on_wifi_fail"
                        self.log("📡 Wi-Fi connectivity appears to be down.")
                    else:
                        recovery_type = "on_site_fail"
                        self.log("🌐 Target site appears to be down.")

                    recovery_cmds = self.settings.get(recovery_type, [])
                    if not recovery_cmds:
                        recovery_cmds = self.settings.get(
                            "on_fail", []
                        )  # fallback legacy key

                    for command in recovery_cmds:
                        self.log(
                            f"⚙️ Running recovery command ({recovery_type}): {command}"
                        )
                        try:
                            subprocess.run(command, shell=True, check=True)
                            self.log(f"✅ Command succeeded: {command}")
                            if log_callback:
                                log_callback(f"✅ Command succeeded: {command}")
                        except subprocess.CalledProcessError as e:
                            self.log(f"❌ Command failed ({command}): {e}")
                            if log_callback:
                                log_callback(f"❌ Command failed ({command}): {e}")

                self.log(msg)
                if log_callback:
                    log_callback(msg)
                time.sleep(interval)

            except Exception as e:
                self.log(f"❌ Watchdog encountered an error: {e}")

        # --- Control Methods ---

    def stop(self):
        """Stop the watchdog loop."""
        self.running = False
        self.log("🛑 Watchdog stopped.")

    def reload_settings(self):
        """Reload settings from disk."""
        self.settings = self.load_settings()
        self.log("🔄 Settings reloaded.")
