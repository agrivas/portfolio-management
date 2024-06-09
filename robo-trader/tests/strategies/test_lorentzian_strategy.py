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

    result = strategy.backtest(datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 3, 1, tzinfo=timezone.utc))
    
    expected_result = {
        'initial_price': 33086.40625,
        'final_price': 49366.96875,
        'price_return': 0.49206197787044337,
        'initial_portfolio_valuation': 1000.0,
        'final_portfolio_valuation': 1000.0,
        'portfolio_return': 0.0
    }
    assert result['initial_price'] == expected_result['initial_price'], "Initial price should match expected value"
    assert result['final_price'] == expected_result['final_price'], "Final price should match expected value"
    assert result['price_return'] == expected_result['price_return'], "Price return should match expected value"
    assert result['initial_portfolio_valuation'] == expected_result['initial_portfolio_valuation'], "Initial portfolio valuation should match expected value"
    assert result['final_portfolio_valuation'] == expected_result['final_portfolio_valuation'], "Final portfolio valuation should match expected value"
    assert result['portfolio_return'] == expected_result['portfolio_return'], "Portfolio return should match expected value"
