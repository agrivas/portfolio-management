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
    def get_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        pass