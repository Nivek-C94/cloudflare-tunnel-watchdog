import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"


def load_settings():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_settings(settings):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(settings, f)
