import os
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"

def get_kraken_credentials() -> tuple:
    if not ENV_FILE.exists():
        return "", ""
    
    api_key = ""
    secret = ""
    
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key.strip() == "KRAKEN_API_KEY":
                    api_key = val.strip()
                elif key.strip() == "KRAKEN_SECRET":
                    secret = val.strip()
    
    return api_key, secret