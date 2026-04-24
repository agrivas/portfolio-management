import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_trading_cycle():
    sys.path.insert(0, str(Path(__file__).parent.parent / "robo-trader"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "backtest_app"))
    
    import pandas as pd
    from robo_trader.feeds import CCXTFeed
    from robo_trader.brokers import CCXTBroker
    from robo_trader.portfolio import Portfolio
    from robo_trader.broker import OrderType, OrderSide

    from config import load_config, get_kraken_credentials
    from state import log_trade, log_error, log_event, save_portfolio_state, load_portfolio_state
    from strategies.loader import load_strategy_class

    config = load_config()
    
    if not config.get("enabled", False):
        return {"status": "disabled", "message": "Trading not enabled"}
    
    log_event("INFO", "CYCLE_START", "Starting trading cycle", f"strategy={config.get('strategy')}, symbol={config.get('symbol')}, interval={config.get('interval')}")
    
    try:
        # Always require real API credentials
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
            interval=config.get("interval", "15m")
        )
        
        symbol = config.get("symbol", "ETH/BTC")
        position_size_pct = config.get("position_size_pct", 0.25)
        
        log_event("INFO", "CONFIG", "Trading parameters", f"position_size_pct={position_size_pct}, stop_pct={config.get('stop_pct', 0.02)}, take_profit_pct={config.get('take_profit_pct', 0.06)}")
        
        # Parse quote currency from symbol (ETH/BTC -> BTC)
        quote_currency = symbol.split("/")[1] if "/" in symbol else symbol
        
        try:
            balance = broker.get_balance()
            free_balance = balance.get('free', {})
            total_balance = balance.get('total', {})
            used_balance = balance.get('used', {})
            
            log_event("INFO", "BROKER_SYNC", "Balance fetched", f"free={free_balance}, total={total_balance}")
            
            available_cash = free_balance.get(quote_currency, 0)
            log_event("INFO", "BROKER_SYNC", f"{quote_currency} balance", f"available={available_cash}")
            
            open_positions = broker.get_open_positions(symbol)
            if open_positions:
                log_event("INFO", "BROKER_SYNC", "Open positions", f"{open_positions}")
                
        except Exception as e:
            log_event("WARNING", "BROKER_SYNC", "Broker sync failed", f"error={str(e)}")
            available_cash = None
        
        # Use broker value if sync succeeded, otherwise use stored state
        portfolio_state = load_portfolio_state()
        stored_cash = portfolio_state.get("cash", 0) if portfolio_state else 0
        
        if available_cash and available_cash > 0:
            cash = available_cash
        else:
            cash = stored_cash
        
        portfolio = Portfolio(broker, cash)
        
        strategy_class = load_strategy_class(config.get("strategy", "adx_ema"))
        strategy = strategy_class(getattr(strategy_class, "PARAMS", {}))
        
        data = feed.get_data(symbol, None, None)
        if data is None or data.empty:
            log_error("DATA", "No data received from feed")
            return {"status": "error", "message": "No data available"}
        
        data = strategy.run(data, strategy.PARAMS) if hasattr(strategy, "run") else data
        
        signal = strategy.evaluate_market(symbol, data, portfolio)
        
        if signal is None:
            logger.warning("Strategy returned no signal, skipping")
            return {"status": "success", "timestamp": datetime.now().isoformat(), "symbol": symbol, "message": "No signal"}
        
        buy_signal = signal.get("buy_signal", False)
        sell_signal = signal.get("sell_signal", False)
        
        current_price = broker.get_price(symbol)
        
        stop_pct = config.get("stop_pct", 0.02)
        take_profit_pct = config.get("take_profit_pct", 0.06)
        
        log_event("INFO", "TRADE_DECISION", f"Evaluating {symbol} at {current_price}", f"position_size_pct={position_size_pct}, cash={cash}")
        
        trades_executed = []
        
        if buy_signal and not portfolio.is_long(symbol):
            log_event("INFO", "ORDER_PREPARE", f"Preparing BUY {symbol}", f"cash_percentage={position_size_pct}, cash={cash}, amount={cash * position_size_pct}, price={current_price}")
            try:
                order = portfolio.open_long(
                    symbol=symbol,
                    cash_percentage=position_size_pct,
                    stop_percentage=stop_pct,
                    take_profit_percentage=take_profit_pct
                )
                if order:
                    log_event("INFO", "ORDER_SUCCESS", f"BUY {symbol} filled", f"order_id={order.id}, quantity={order.quantity}, price={current_price}")
                    log_trade(symbol, "BUY", order.quantity, current_price, "FILLED", order.id)
                    trades_executed.append({"side": "BUY", "quantity": order.quantity})
            except Exception as e:
                log_event("ERROR", "ORDER_FAILED", f"BUY {symbol} rejected", f"error={str(e)}")
                raise
        
        elif sell_signal and portfolio.is_long(symbol):
            log_event("INFO", "ORDER_PREPARE", f"Preparing SELL {symbol}", f"current_position={portfolio.positions}")
            try:
                order = portfolio.close_long(symbol)
                if order:
                    log_event("INFO", "ORDER_SUCCESS", f"SELL {symbol} filled", f"order_id={order.id}, quantity={order.quantity}, price={current_price}")
                    log_trade(symbol, "SELL", order.quantity, current_price, "FILLED", order.id)
                    trades_executed.append({"side": "SELL", "quantity": order.quantity})
            except Exception as e:
                log_event("ERROR", "ORDER_FAILED", f"SELL {symbol} rejected", f"error={str(e)}")
                raise
        
        save_portfolio_state(portfolio.cash, portfolio.asset_holdings)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "price": current_price,
            "buy_signal": buy_signal,
            "sell_signal": sell_signal,
            "trades": trades_executed,
            "portfolio_cash": portfolio.cash
        }
        
    except Exception as e:
        logger.exception("Trading cycle failed")
        log_error("RUNTIME", str(e))
        log_event("ERROR", "CYCLE_FAILED", "Trading cycle exception", f"error={str(e)}")
        return {"status": "error", "message": str(e)}