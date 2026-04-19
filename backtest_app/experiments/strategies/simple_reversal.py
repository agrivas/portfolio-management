import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robo-trader'))

from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd

PARAMS = {
    'sma_period': 20,
    'rsi_period': 14,
    'rsi_overbought': 60,
    'position_size': 0.25,
    'trailing_stop': 0.02,
    'take_profit': 0.10,
}


class SimpleReversalStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.sma_period = params.get('sma_period', PARAMS['sma_period'])
        self.rsi_period = params.get('rsi_period', PARAMS['rsi_period'])
        self.rsi_overbought = params.get('rsi_overbought', PARAMS['rsi_overbought'])
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.trailing_stop = params.get('trailing_stop', PARAMS['trailing_stop'])
        self.take_profit = params.get('take_profit', PARAMS['take_profit'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < max(self.sma_period, self.rsi_period):
            return

        data = prices.copy()

        # Simple SMA
        data['SMA'] = data['close'].rolling(window=self.sma_period).mean()

        # Simple RSI using ta library
        try:
            import ta
            data['RSI'] = ta.momentum.rsi(data['close'], window=self.rsi_period)
        except:
            # Fallback: simple RSI
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))

        last_price = data['close'].iloc[-1]
        last_sma = data['SMA'].iloc[-1]
        last_rsi = data['RSI'].iloc[-1]

        if pd.isna(last_sma) or pd.isna(last_rsi):
            return

        if last_price > last_sma and last_rsi < self.rsi_overbought:
            portfolio.open_long(
                symbol,
                self.position_size,
                self.trailing_stop,
                self.take_profit
            )