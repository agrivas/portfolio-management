import pytest
from datetime import datetime, timezone, timedelta
from robo_trader.strategies.lorentzian_strategy import LorentzianStrategy, LorentzianSettings
from robo_trader.portfolio import Portfolio
from robo_trader.price_provider import Interval
from robo_trader.exchange import DummyExchange
from robo_trader.price_providers.yfinance import YFinancePriceProvider
import pandas as pd

SYMBOL = "BTC-GBP"

@pytest.fixture
def setup_strategy():
    price_provider = YFinancePriceProvider()
    exchange = DummyExchange({SYMBOL: 100.0}, 0.004)
    portfolio = Portfolio(SYMBOL, exchange, inception_date=datetime(2000, 1, 1, tzinfo=timezone.utc))
    settings = LorentzianSettings()
    strategy = LorentzianStrategy(SYMBOL, price_provider, Interval.ONE_HOUR, portfolio, settings)
    
    return strategy, price_provider, portfolio

def test_backtest(setup_strategy):
    strategy, _, _ = setup_strategy

    start_date = (datetime.now(timezone.utc) - timedelta(days=366)).replace(minute=0, second=0, microsecond=0)
    end_date = (datetime.now(timezone.utc) - timedelta(days=359)).replace(minute=0, second=0, microsecond=0)

    result = strategy.backtest(start_date, end_date, period = 24)
    
    assert isinstance(result['initial_price'], (int, float))
    assert isinstance(result['final_price'], (int, float))
    assert isinstance(result['price_return'], (int, float))
    assert isinstance(result['initial_portfolio_valuation'], (int, float))
    assert isinstance(result['final_portfolio_valuation'], (int, float))
    assert isinstance(result['portfolio_return'], (int, float))
    assert len(result['discrete_returns']) == 7
