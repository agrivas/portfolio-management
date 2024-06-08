# tests/test_dummy_signal_generator.py

import pytest
from robo_trader.signal_generator import DummySignalGenerator

@pytest.fixture
def dummy_signal_generator():
    return DummySignalGenerator("XBTGBP")

def test_generate_signal(dummy_signal_generator):
    dummy_signal_generator.add_historical_data("2024-01-01", 5000, 5200, 4900, 5100, 1000)
    assert dummy_signal_generator.generate_signal() in ["BUY", "SELL"]

def test_update_prediction(dummy_signal_generator):
    dummy_signal_generator.update_prediction()  # Dummy method, should not raise error
