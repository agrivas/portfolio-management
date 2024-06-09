import pytest
from datetime import datetime, timezone
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
    strategy = LorentzianStrategy(SYMBOL, price_provider, Interval.ONE_DAY, portfolio, settings)
    
    return strategy, price_provider, portfolio

def test_backtest(setup_strategy):
    strategy, _, _ = setup_strategy

    result = strategy.backtest(datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 3, 1, tzinfo=timezone.utc), period = 7)
    
    assert result['initial_price'] == 33086.40625
    assert result['final_price'] == 49366.96875
    assert result['price_return'] == 0.49206197787044337
    assert result['initial_portfolio_valuation'] == 1000.0
    assert result['final_portfolio_valuation'] == 1000.0
    assert result['portfolio_return'] == 0.0
    assert result['portfolio_return'] == 0.0
    assert len(result['discrete_returns']) == 8
