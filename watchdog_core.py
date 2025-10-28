import logging
import os
import requests
import subprocess
import time
import yaml
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
LOG_PATH = os.path.join(os.path.dirname(__file__), "watchdog.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class WatchdogCore:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.load_config()
        self.running = False

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")
        logging.info(msg)

    def load_config(self):
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def run_command(self, cmd):
        try:
            subprocess.run(cmd, shell=True, check=True)
            self.log(f"✅ Ran command: {cmd}")
        except subprocess.CalledProcessError:
            self.log(f"⚠️ Command failed: {cmd}")

    def perform_actions(self, actions):
        for cmd in actions:
            self.run_command(cmd)

    def has_internet(self):
        try:
            requests.get("https://1.1.1.1", timeout=5)
            return True
        except requests.RequestException:
            return False

    def site_online(self, url):
        try:
            r = requests.get(url, timeout=5)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def start(self, callback=None):
        self.running = True
        failures = 0
        last_state = "unknown"

        while self.running:
            self.load_config()
            target_url = self.config["target_url"]
            failure_threshold = self.config.get("failure_threshold", 3)
            check_interval = self.config.get("check_interval", 30)

            msg = "🔍 Checking system status..."
            self.log(msg)
            if callback:
                callback(msg)

            if not self.has_internet():
                msg = "❌ Internet down. Attempting reconnection..."
                self.log(msg)
                if callback:
                    callback(msg)
                self.perform_actions(self.config["actions"]["on_internet_down"])
                time.sleep(check_interval)
                continue

            if not self.site_online(target_url):
                failures += 1
                msg = f"⚠️ Site appears down ({failures}/{failure_threshold})"
                self.log(msg)
                if callback:
                    callback(msg)

                if failures >= failure_threshold:
                    msg = "🚨 Threshold reached. Restarting services..."
                    self.log(msg)
                    if callback:
                        callback(msg)
                    self.perform_actions(self.config["actions"]["on_site_down"])
                    failures = 0
            else:
                if last_state != "online":
                    msg = "🔁 Site recovered. Running recovery actions..."
                    self.log(msg)
                    if callback:
                        callback(msg)
                    self.perform_actions(self.config["actions"]["on_recovery"])
                failures = 0
                last_state = "online"
                msg = "✅ Site is healthy."
                self.log(msg)
                if callback:
                    callback(msg)

            time.sleep(check_interval)

    def stop(self):
        self.running = False
        self.log("🛑 Watchdog stopped.")
