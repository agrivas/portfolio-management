# robo_trader/price_provider.py

from datetime import datetime
from abc import ABC, abstractmethod
import pandas as pd

from enum import Enum

class Interval(Enum):
    ONE_MINUTE = '1m'
    FIVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    THIRTY_MINUTES = '30m'
    ONE_HOUR = '1h'
    ONE_DAY = '1d'
    ONE_WEEK = '1wk'
    ONE_MONTH = '1mo'

class PriceProvider(ABC):
    @abstractmethod
    def get_prices(self, symbol: str, interval: Interval, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        Abstract method to fetch price data for a given symbol over a specified interval and time range.

        :param symbol: The trading symbol for which prices are to be fetched.
        :param interval: The interval at which prices should be fetched (e.g., '1m', '5m', '1h').
        :param start_date: The starting date from which prices should be fetched (inclusive).
        :param end_date: The ending date until which prices should be fetched (inclusive).
        :return: A DataFrame containing the price data.
        """
        pass
