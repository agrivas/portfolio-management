import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robo-trader'))

from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'position_size': 1.0,
    'stop_loss': 0.05,
    'take_profit': 0.05,
    'adx_length': 12,
    'adx_threshold': 30,
    'ema_length_very_short': 6,
    'ema_length_short': 12,
    'ema_length_long': 72,
    'rsi_length': 48,
    'rsi_oversold': 20,
}


class AdxEmaRsiStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.stop_loss = params.get('stop_loss', PARAMS['stop_loss'])
        self.take_profit = params.get('take_profit', PARAMS['take_profit'])
        self.adx_length = params.get('adx_length', PARAMS['adx_length'])
        self.adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])
        self.ema_length_very_short = params.get('ema_length_very_short', PARAMS['ema_length_very_short'])
        self.ema_length_short = params.get('ema_length_short', PARAMS['ema_length_short'])
        self.ema_length_long = params.get('ema_length_long', PARAMS['ema_length_long'])
        self.rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
        self.rsi_oversold = params.get('rsi_oversold', PARAMS['rsi_oversold'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        min_len = self.adx_length + max(self.ema_length_long, self.rsi_length)
        if len(prices) < min_len:
            return

        data = prices.copy()

        adx = pta.adx(data['high'], data['low'], data['close'], length=self.adx_length)
        data['adx'] = adx[f'ADX_{self.adx_length}']
        data['ema_very_short'] = pta.ema(data['close'], length=self.ema_length_very_short)
        data['ema_short'] = pta.ema(data['close'], length=self.ema_length_short)
        data['ema_long'] = pta.ema(data['close'], length=self.ema_length_long)

        last = data.iloc[-1]

        if pd.isna(last['adx']) or pd.isna(last['ema_long']) or pd.isna(last['ema_short']):
            return

        data['rsi'] = pta.rsi(data['close'], length=self.rsi_length)
        last['rsi'] = data['rsi'].iloc[-1]

        if pd.isna(last['rsi']):
            return

        strong_trend = last['adx'] > self.adx_threshold
        rsi_oversold = last['rsi'] < self.rsi_oversold
        ema_buy = (last['ema_short'] > last['ema_long']) and (last['ema_very_short'] > last['ema_short']) and (last['close'] > last['ema_short'])

        if strong_trend and rsi_oversold and ema_buy:
            portfolio.open_long(symbol, self.position_size, None, self.take_profit, self.stop_loss)