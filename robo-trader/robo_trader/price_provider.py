# robo_trader/price_provider.py

from datetime import datetime
from abc import ABC, abstractmethod
import pandas as pd

class PriceProvider(ABC):
    def __init__(self, symbol: str):
        """
        Initialize the PriceProvider with a specific symbol.

        :param symbol: The trading symbol for which prices will be provided.
        """
        self.symbol = symbol

    @abstractmethod
    def get_prices(self, symbol: str, interval: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """
        Abstract method to fetch price data for a given symbol over a specified interval and time range.

        :param symbol: The trading symbol for which prices are to be fetched.
        :param interval: The interval at which prices should be fetched (e.g., '1m', '5m', '1h').
        :param start_date: The starting date from which prices should be fetched (inclusive).
        :param end_date: The ending date until which prices should be fetched (inclusive).
        :return: A DataFrame containing the price data.
        """
        pass
