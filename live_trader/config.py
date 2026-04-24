import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / ".env"

def load_env():
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

def load_config() -> dict:
    load_env()
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_kraken_credentials() -> tuple:
    load_env()
    api_key = os.getenv("KRAKEN_API_KEY", "")
    secret = os.getenv("KRAKEN_SECRET", "")
    return api_key, secret