import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

STATE_DIR = Path(__file__).parent / "state"
TRADE_LOG = STATE_DIR / "trade_log.csv"
ERROR_LOG = STATE_DIR / "error_log.csv"
EVENT_LOG = STATE_DIR / "event_log.csv"
PORTFOLIO_STATE = STATE_DIR / "portfolio.json"

logger = logging.getLogger(__name__)

def get_portfolio_state():
    if not PORTFOLIO_STATE.exists():
        return None
    with open(PORTFOLIO_STATE) as f:
        return json.load(f)

def save_portfolio_state(state):
    with open(PORTFOLIO_STATE, "w") as f:
        json.dump(state, f, indent=4, default=str)

def log_trade(symbol: str, side: str, quantity: float, price: float, status: str, order_id: str, error: str = ""):
    file_exists = TRADE_LOG.exists()
    with open(TRADE_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime", "symbol", "side", "quantity", "price", "status", "order_id", "error"])
        writer.writerow([
            datetime.now().isoformat(),
            symbol,
            side,
            quantity,
            price,
            status,
            order_id,
            error
        ])

def log_error(error_type: str, message: str, details: str = ""):
    file_exists = ERROR_LOG.exists()
    with open(ERROR_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime", "error_type", "message", "details"])
        writer.writerow([
            datetime.now().isoformat(),
            error_type,
            message,
            details
        ])
    logger.error(f"{error_type}: {message} | {details}")

def log_event(severity: str, event_type: str, message: str, details: str = ""):
    file_exists = EVENT_LOG.exists()
    with open(EVENT_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime", "severity", "event_type", "message", "details"])
        writer.writerow([
            datetime.now().isoformat(),
            severity,
            event_type,
            message,
            details
        ])
    if severity == "ERROR":
        logger.error(f"{event_type}: {message} | {details}")
    elif severity == "WARNING":
        logger.warning(f"{event_type}: {message} | {details}")
    else:
        logger.info(f"{event_type}: {message} | {details}")

def get_event_log(limit: int = 100) -> list:
    if not EVENT_LOG.exists():
        return []
    with open(EVENT_LOG) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[-limit:] if len(rows) > limit else rows

def get_trade_log(limit: int = 50) -> list:
    if not TRADE_LOG.exists():
        return []
    with open(TRADE_LOG) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[-limit:] if len(rows) > limit else rows

def get_error_log(limit: int = 50) -> list:
    if not ERROR_LOG.exists():
        return []
    with open(ERROR_LOG) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[-limit:] if len(rows) > limit else rows