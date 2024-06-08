# robo_trader/price_provider.py

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import pandas as pd
import random
from .types import Ohlcv

class PriceProvider(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractmethod
    def get_latest_price(self) -> pd.Series:
        pass

    @abstractmethod
    def get_latest_ohlcv(self) -> pd.DataFrame:
        pass

class DummyPriceProvider(PriceProvider):
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.current_Ohlcv = pd.Series({
            Ohlcv.DATE: datetime.now(timezone.utc),
            Ohlcv.OPEN: random.uniform(90, 110),
            Ohlcv.HIGH: random.uniform(90, 110),
            Ohlcv.LOW: random.uniform(90, 110),
            Ohlcv.CLOSE: random.uniform(90, 110),
            Ohlcv.VOLUME: random.randint(1000, 10000)
        })

    def get_latest_price(self) -> pd.Series:
        # Simulate getting the latest Ohlcv price for the given symbol
        self.current_Ohlcv[Ohlcv.OPEN] = random.uniform(90, 110)
        self.current_Ohlcv[Ohlcv.HIGH] = random.uniform(90, 110)
        self.current_Ohlcv[Ohlcv.LOW] = random.uniform(90, 110)
        self.current_Ohlcv[Ohlcv.CLOSE] = random.uniform(90, 110)
        self.current_Ohlcv[Ohlcv.VOLUME] = random.randint(1000, 10000)
        self.current_Ohlcv[Ohlcv.DATE] = datetime.now(timezone.utc)
        return self.current_Ohlcv

    def get_latest_ohlcv(self) -> pd.DataFrame:
        # Simulate getting the latest Ohlcv for the given symbol
        now = datetime.now(timezone.utc)
        Ohlcv_data = {
            Ohlcv.DATE: [now],
            Ohlcv.OPEN: [random.uniform(90, 110)],
            Ohlcv.HIGH: [random.uniform(90, 110)],
            Ohlcv.LOW: [random.uniform(90, 110)],
            Ohlcv.CLOSE: [random.uniform(90, 110)],
            Ohlcv.VOLUME: [random.randint(1000, 10000)]
        }
        return pd.DataFrame(Ohlcv_data)
