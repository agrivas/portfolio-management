from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime

class Ohlcv:
    DATE = 'date'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'

class Feed(ABC):
    @abstractmethod
    def get_live_data(self, symbol: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        pass