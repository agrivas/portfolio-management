from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
from dataclasses import dataclass
import pandas as pd
import ta

@dataclass
class SimpleReversalSettings:
    sma_period: int = 20
    rsi_period: int = 14
    rsi_overbought: int = 60
    position_size: float = 0.25
    trailing_stop: float = 0.02
    take_profit: float = None

class SimpleReversalStrategy(Strategy):
    def __init__(self, settings: SimpleReversalSettings):
        super().__init__()
        self.settings = settings

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < self.settings.sma_period:
            return

        data = prices.copy()

        data['SMA'] = data['close'].rolling(window=self.settings.sma_period).mean()
        data['RSI'] = ta.momentum.rsi(data['close'], window=self.settings.rsi_period)

        last_price = data['close'].iloc[-1]
        last_sma = data['SMA'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1]

        if last_price > last_sma and last_rsi < self.settings.rsi_overbought:
            portfolio.open_long(symbol, self.settings.position_size, self.settings.trailing_stop, self.settings.take_profit)
