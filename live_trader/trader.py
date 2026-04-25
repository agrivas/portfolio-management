import logging
from datetime import datetime

from robo_trader.feeds import CCXTFeed
from robo_trader.brokers import CCXTBroker
from robo_trader.portfolio import Portfolio
from robo_trader.trader import Trader

from config import get_kraken_credentials
from state import get_portfolio_state, save_portfolio_state, log_trade, log_error, log_event, PORTFOLIO_STATE
from strategies.loader import load_strategy_class

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def run_trading_cycle():
    portfolio_state = get_portfolio_state()
    if not portfolio_state:
        return {"status": "error", "message": "No portfolio configured. Visit UI to set up your preferences."}
    
    settings = portfolio_state.get("settings", {})
    state = portfolio_state.get("state", {})
    
    symbol = settings.get("symbol")
    strategy_name = settings.get("strategy", "adx_ema")
    interval = settings.get("interval", "15m")
    position_size_pct = settings.get("position_size_pct", 0.5)
    stop_pct = settings.get("stop_pct", 0.01)
    take_profit_pct = settings.get("take_profit_pct", 0.1)
    
    log_event("INFO", "CYCLE_START", "Starting trading cycle", f"strategy={strategy_name}, symbol={symbol}, interval={interval}")
    
    try:
        api_key, secret = get_kraken_credentials()
        if not api_key or not secret:
            log_error("CONFIG", "Missing Kraken API credentials")
            log_event("ERROR", "CREDENTIALS", "Missing Kraken API credentials", "")
            return {"status": "error", "message": "Missing API credentials"}
        
        broker = CCXTBroker(
            exchange_id="kraken",
            api_key=api_key,
            secret=secret
        )
        
        feed = CCXTFeed(
            exchange_id="kraken",
            api_key=api_key,
            secret=secret,
            interval=interval
        )
        
        log_event("INFO", "CONFIG", "Trading parameters", f"position_size_pct={position_size_pct}, stop_pct={stop_pct}, take_profit_pct={take_profit_pct}")
        
        portfolio = Portfolio.from_directory(broker, str(PORTFOLIO_STATE.parent))
        log_event("INFO", "PORTFOLIO", "Loaded portfolio", f"cash={portfolio.cash}, holdings={portfolio.asset_holdings}")
        
        portfolio.sync_from_broker(symbol)
        portfolio.save()
        
        log_event("INFO", "BROKER_SYNC", "Portfolio synced", f"cash={portfolio.cash}, holdings={portfolio.asset_holdings}")
        
        strategy_class = load_strategy_class(strategy_name)
        strategy = strategy_class(getattr(strategy_class, "PARAMS", {}))
        
        trader = Trader(
            symbol=symbol,
            initial_cash=portfolio.cash,
            feed=feed,
            strategy=strategy,
            broker=broker
        )
        
        result = trader.run_cycle()
        
        if result.get("status") == "success":
            portfolio.save()
            for trade in result.get("trades", []):
                log_trade(symbol, trade["side"], trade["quantity"], trade["price"], "FILLED", trade["order_id"])
        
        portfolio_state["state"]["cash"] = portfolio.cash
        portfolio_state["state"]["asset_holdings"] = portfolio.asset_holdings
        save_portfolio_state(portfolio_state)
        
        return result
        
    except FileNotFoundError as e:
        log_event("ERROR", "PORTFOLIO", "Portfolio not found", str(e))
        return {"status": "error", "message": "No portfolio configured. Visit UI to set up your preferences."}
    except Exception as e:
        logger.exception("Trading cycle failed")
        log_error("RUNTIME", str(e))
        log_event("ERROR", "CYCLE_FAILED", "Trading cycle exception", f"error={str(e)}")
        return {"status": "error", "message": str(e)}