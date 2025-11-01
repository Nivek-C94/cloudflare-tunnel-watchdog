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
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200 and r.text.strip():
                        msg = f"✅ Site online: {url}"
                        success = True
                    else:
                        msg = f"⚠️ Site reachable but not responding correctly (status {r.status_code})"
                        success = False
                except requests.ConnectionError:
                    msg = f"❌ Connection failed: {url}"
                    success = False
                except requests.Timeout:
                    msg = f"⏱️ Connection timed out: {url}"
                    success = False
                except Exception as e:
                    msg = f"❌ Unexpected error: {e}"
                    success = False

                import subprocess, platform

                def run_commands(command_list, label):
                    for raw in command_list:
                        if not raw.strip():
                            continue
                        commands = [
                            c.strip()
                            for c in raw.replace(";", "\n").splitlines()
                            if c.strip()
                        ]
                        for command in commands:
                            self.log(f"🔁 Running {label} command: {command}")
                            try:
                                if platform.system() == "Windows":
                                    completed = subprocess.run(
                                        [
                                            "powershell",
                                            "-NoProfile",
                                            "-ExecutionPolicy",
                                            "Bypass",
                                            "-Command",
                                            f"& {{ {command} }}",
                                        ],
                                        capture_output=True,
                                        text=True,
                                        encoding="utf-8",
                                    )
                                else:
                                    completed = subprocess.run(
                                        ["/bin/bash", "-c", command],
                                        capture_output=True,
                                        text=True,
                                        encoding="utf-8",
                                    )

                                if completed.returncode == 0:
                                    self.log(f"✅ Command succeeded: {command}")
                                    if completed.stdout:
                                        self.log(completed.stdout.strip())
                                else:
                                    self.log(
                                        f"❌ Command failed ({command}) → Exit {completed.returncode}"
                                    )
                                    if completed.stderr:
                                        self.log(completed.stderr.strip())
                            except Exception as e:
                                self.log(f"💥 Command error ({command}): {e}")

                run_commands(self.settings.get("on_site_fail", []), "on-site-fail")
                run_commands(self.settings.get("on_wifi_fail", []), "on-wifi-fail")
                run_commands(self.settings.get("on_recovery", []), "on-recovery")
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
