from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'position_size': 1.0,
    'stop_loss': 0.05,
    'take_profit': 0.10,
    'sma_length_long': 72,
    'drop_period': 12,
    'recovery_period': 6,
    'drop_threshold': 2,
    'recovery_threshold': 2,
    'rsi_length': 14,
    'rsi_not_overbought': 70,
}


class SmaBuyDipStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.stop_loss = params.get('stop_loss', PARAMS['stop_loss'])
        self.take_profit = params.get('take_profit', PARAMS['take_profit'])
        self.sma_length_long = params.get('sma_length_long', PARAMS['sma_length_long'])
        self.drop_period = params.get('drop_period', PARAMS['drop_period'])
        self.recovery_period = params.get('recovery_period', PARAMS['recovery_period'])
        self.drop_threshold = params.get('drop_threshold', PARAMS['drop_threshold'])
        self.recovery_threshold = params.get('recovery_threshold', PARAMS['recovery_threshold'])
        self.rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
        self.rsi_not_overbought = params.get('rsi_not_overbought', PARAMS['rsi_not_overbought'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        min_len = self.sma_length_long + self.drop_period + self.recovery_period + self.rsi_length
        if len(prices) < min_len:
            return

        data = prices.copy()

        data['sma_long'] = pta.sma(data['close'], length=self.sma_length_long)
        data['sma_long_drop'] = data['sma_long'].pct_change(periods=self.drop_period)
        average_drop = data['sma_long_drop'].mean()
        data['sma_long_recovery'] = data['sma_long'].pct_change(periods=self.recovery_period)
        average_recovery = data['sma_long_recovery'].mean()
        data['rsi'] = pta.rsi(data['close'], length=self.rsi_length)

        last = data.iloc[-1]

        if pd.isna(last['sma_long']) or pd.isna(last['rsi']) or pd.isna(average_drop) or pd.isna(average_recovery):
            return

        sma_dropped = last['sma_long_drop'] < -self.drop_threshold * abs(average_drop)
        sma_recovering = last['sma_long_recovery'] > self.recovery_threshold * abs(average_recovery)
        rsi_ok = last['rsi'] < self.rsi_not_overbought

        if sma_dropped and sma_recovering and rsi_ok:
            portfolio.open_long(symbol, self.position_size, None, self.take_profit, self.stop_loss)