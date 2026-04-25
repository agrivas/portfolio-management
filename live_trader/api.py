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
from state import get_portfolio_state, save_portfolio_state, get_event_log, get_trade_log, log_event, PORTFOLIO_STATE
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
    portfolio_state = get_portfolio_state()
    
    result = {
        "timestamp": datetime.now().isoformat(),
    }
    
    if portfolio_state:
        result["settings"] = portfolio_state.get("settings", {})
        result["state"] = portfolio_state.get("state", {})
    else:
        result["settings"] = None
        result["state"] = None
    
    return result


@app.get("/logs")
def logs(
    severity: str = Query(default=None, description="Filter by severity (INFO,WARNING,ERROR)"),
    limit: int = Query(default=100, description="Max number of logs")
):
    events = get_event_log(limit)
    
    if severity:
        severities = severity.split(",") if "," in severity else [severity]
        events = [e for e in events if e.get("severity") in severities]
    
    return events


@app.get("/trades")
def trades(limit: int = Query(default=50)):
    return get_trade_log(limit)


@app.get("/config")
def get_config():
    portfolio_state = get_portfolio_state()
    if portfolio_state:
        return portfolio_state.get("settings", {})
    return {}


@app.post("/config")
def update_config(config_update: ConfigUpdate):
    portfolio_state = get_portfolio_state()
    
    if not portfolio_state:
        portfolio_state = {
            "uuid": "live-trader-v1",
            "autosave": True,
            "settings": {},
            "state": {
                "cash": 0,
                "asset_holdings": {},
                "orders": {},
                "positions": [],
                "valuation_history": [],
                "processed_trades": []
            }
        }
    
    settings = portfolio_state.setdefault("settings", {})
    
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
    
    PORTFOLIO_STATE.parent.mkdir(parents=True, exist_ok=True)
    save_portfolio_state(portfolio_state)
    log_event("INFO", "CONFIG", "Settings updated", str(settings))
    return {"success": True, "settings": settings}


@app.get("/strategies")
def strategies():
    return list_strategies()