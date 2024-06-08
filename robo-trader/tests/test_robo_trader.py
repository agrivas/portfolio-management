# tests/test_robo_trader.py

import pytest
from unittest.mock import MagicMock
from robo_trader.robo_trader import RoboTrader
from robo_trader.price_provider import DummyPriceProvider
from robo_trader.signal_generator import DummySignalGenerator
from robo_trader.portfolio_manager import PortfolioManager
from robo_trader.types import Ohlcv

@pytest.fixture
def robo_trader():
    symbol = "XBTGBP"
    price_provider = DummyPriceProvider(symbol)
    signal_generator = DummySignalGenerator(symbol)
    portfolio_manager = PortfolioManager(symbol)
    trader = RoboTrader(symbol, price_provider, signal_generator, portfolio_manager)
    trader.price_provider.get_latest_ohlcv = MagicMock(return_value={
        'date': '2024-01-01T00:00:00Z',
        'open': 100.0,
        'high': 105.0,
        'low': 95.0,
        'close': 100.0,
        'volume': 1000
    })
    trader.signal_generator.generate_signal = MagicMock(return_value="BUY")
    return trader

def test_robo_trader_update(robo_trader):
    robo_trader.run(exit_after = 3)
    assert not robo_trader.signal_generator.historical_data.empty
    assert robo_trader.signal_generator.historical_data.iloc[0][Ohlcv.CLOSE] == 100.0
    assert robo_trader.portfolio_manager.tokens > 0
