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


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    logging.info(msg)


def run_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        log(f"✅ Ran command: {cmd}")
    except subprocess.CalledProcessError:
        log(f"⚠️ Command failed: {cmd}")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def has_internet():
    try:
        requests.get("https://1.1.1.1", timeout=5)
        return True
    except requests.RequestException:
        return False


def site_online(url):
    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False

    log(
        "💡 Reminder: This service is set to auto-run on boot via systemd (cloudflare-watchdog.service)."
    )
    for cmd in actions:
        run_command(cmd)


def main():
    cfg = load_config()
    target_url = cfg["target_url"]
    failure_threshold = cfg.get("failure_threshold", 3)
    check_interval = cfg.get("check_interval", 30)

    failures = 0
    last_state = "unknown"

    while True:
        cfg = load_config()  # Reload config dynamically
        log("🔍 Checking system status...")

        if not has_internet():
            log("❌ Internet down. Attempting reconnection...")
            perform_actions(cfg["actions"]["on_internet_down"])
            time.sleep(check_interval)
            continue

        if not site_online(target_url):
            failures += 1
            log(f"⚠️ Site appears down ({failures}/{failure_threshold})")

            if failures >= failure_threshold:
                log("🚨 Threshold reached. Restarting services...")
                perform_actions(cfg["actions"]["on_site_down"])
                failures = 0
        else:
            if last_state != "online":
                perform_actions(cfg["actions"]["on_recovery"])
            failures = 0
            last_state = "online"
            log("✅ Site is healthy.")

        time.sleep(check_interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Watchdog stopped manually.")
