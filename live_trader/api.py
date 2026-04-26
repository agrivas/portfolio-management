import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Live Trader API", version="1.0.0")

from config import get_kraken_credentials
from state import get_settings, save_settings, get_event_log, get_trade_log, log_event, SETTINGS_FILE, PORTFOLIO_FILE, is_trader_paused, set_trader_paused
from trader import run_trading_cycle
from strategies.loader import list_strategies


class ConfigUpdate(BaseModel):
    strategy: Optional[str] = None
    symbol: Optional[str] = None
    interval: Optional[str] = None
    position_size_pct: Optional[float] = None
    stop_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


@app.get("/")
def root():
    return {"message": "Live Trader API", "version": "1.0.0", "endpoints": ["/trading-cycle", "/status", "/logs", "/trades", "/config"]}


@app.post("/trading-cycle")
def trading_cycle():
    return run_trading_cycle()


@app.get("/status")
def status():
    settings = get_settings()
    
    portfolio_state = {}
    if PORTFOLIO_FILE.exists():
        with open(PORTFOLIO_FILE) as f:
            portfolio_state = json.load(f)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "running": not is_trader_paused(),
    }
    
    result["settings"] = settings if settings else {}
    result["cash"] = portfolio_state.get("cash", 0)
    result["holdings"] = portfolio_state.get("asset_holdings", {})
    
    return result


@app.post("/trading/pause")
def trading_pause():
    set_trader_paused(True)
    log_event("INFO", "TRADER", "Trader paused", "")
    return {"success": True, "running": False}


@app.post("/trading/start")
def trading_start():
    set_trader_paused(False)
    log_event("INFO", "TRADER", "Trader started", "")
    return {"success": True, "running": True}


@app.get("/logs")
def logs(
    severity: str = Query(default=None, description="Filter by severity (INFO,WARNING,ERROR)"),
    limit: int = Query(default=100, description="Max number of logs")
):
    events = get_event_log(limit)
    
    if severity:
        severities = severity.split(",") if "," in severity else [severity]
        events = [e for e in events if e.get("severity") in severities]
    
    return events if events else []


@app.get("/trades")
def trades(limit: int = Query(default=50)):
    trades = get_trade_log(limit)
    return trades if trades else []


@app.get("/config")
def get_config():
    return get_settings()


@app.post("/config")
def update_config(config_update: ConfigUpdate):
    settings = get_settings()
    
    if not settings:
        settings = {}
    
    if config_update.strategy is not None:
        settings["strategy"] = config_update.strategy
    if config_update.symbol is not None:
        settings["symbol"] = config_update.symbol
    if config_update.interval is not None:
        settings["interval"] = config_update.interval
    if config_update.position_size_pct is not None:
        settings["position_size_pct"] = config_update.position_size_pct
    if config_update.stop_pct is not None:
        settings["stop_pct"] = config_update.stop_pct
    if config_update.take_profit_pct is not None:
        settings["take_profit_pct"] = config_update.take_profit_pct
    
    save_settings(settings)
    log_event("INFO", "CONFIG", "Settings updated", str(settings))
    return {"success": True, "settings": settings}


@app.get("/strategies")
def strategies():
    return list_strategies()