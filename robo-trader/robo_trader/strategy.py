from abc import ABC, abstractmethod
from .trader import Trader
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def evaluate_market(self, prices: pd.DataFrame, trader: Trader):
        pass