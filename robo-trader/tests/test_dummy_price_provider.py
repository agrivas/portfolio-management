# tests/test_price_provider.py

import pytest
from robo_trader.price_provider import DummyPriceProvider
from robo_trader.types import Ohlcv
from datetime import datetime, timezone
import pandas as pd

@pytest.fixture
def dummy_price_provider():
    return DummyPriceProvider("XBTGBP")

def test_get_latest_price(dummy_price_provider):
    price = dummy_price_provider.get_latest_price()
    assert isinstance(price, pd.Series)
    assert Ohlcv.OPEN in price
    assert Ohlcv.HIGH in price
    assert Ohlcv.LOW in price
    assert Ohlcv.CLOSE in price
    assert Ohlcv.VOLUME in price
    assert Ohlcv.DATE in price
    assert 90 <= price[Ohlcv.OPEN] <= 110
    assert 90 <= price[Ohlcv.HIGH] <= 110
    assert 90 <= price[Ohlcv.LOW] <= 110
    assert 90 <= price[Ohlcv.CLOSE] <= 110
    assert 1000 <= price[Ohlcv.VOLUME] <= 10000
    assert isinstance(price[Ohlcv.DATE], datetime)
    assert price[Ohlcv.DATE].tzinfo is not None  # Ensure it's timezone aware

def test_get_latest_ohlcv(dummy_price_provider):
    ohlcv = dummy_price_provider.get_latest_ohlcv()
    assert isinstance(ohlcv, pd.DataFrame)
    assert Ohlcv.DATE in ohlcv.columns
    assert Ohlcv.OPEN in ohlcv.columns
    assert Ohlcv.HIGH in ohlcv.columns
    assert Ohlcv.LOW in ohlcv.columns
    assert Ohlcv.CLOSE in ohlcv.columns
    assert Ohlcv.VOLUME in ohlcv.columns
    assert 90 <= ohlcv[Ohlcv.OPEN].iloc[0] <= 110
    assert 90 <= ohlcv[Ohlcv.HIGH].iloc[0] <= 110
    assert 90 <= ohlcv[Ohlcv.LOW].iloc[0] <= 110
    assert 90 <= ohlcv[Ohlcv.CLOSE].iloc[0] <= 110
    assert 1000 <= ohlcv[Ohlcv.VOLUME].iloc[0] <= 10000
    assert isinstance(ohlcv[Ohlcv.DATE].iloc[0], datetime)
    assert ohlcv[Ohlcv.DATE].iloc[0].tzinfo is not None  # Ensure it's timezone aware
