from abc import ABC, abstractmethod
from .portfolio import Portfolio
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        pass