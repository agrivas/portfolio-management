import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robo-trader'))

from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'position_size': 1.0,
    'adx_length': 24,
    'adx_threshold': 30,
    'ema_length_short': 24,
    'ema_length_long': 168,
}


class AdxEmaStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.adx_length = params.get('adx_length', PARAMS['adx_length'])
        self.adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])
        self.ema_length_short = params.get('ema_length_short', PARAMS['ema_length_short'])
        self.ema_length_long = params.get('ema_length_long', PARAMS['ema_length_long'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < self.adx_length + self.ema_length_long:
            return

        data = prices.copy()

        adx = pta.adx(data['high'], data['low'], data['close'], length=self.adx_length)
        data['adx'] = adx[f'ADX_{self.adx_length}']
        data['ema_short'] = pta.ema(data['close'], length=self.ema_length_short)
        data['ema_long'] = pta.ema(data['close'], length=self.ema_length_long)

        last = data.iloc[-1]

        if pd.isna(last['adx']) or pd.isna(last['ema_short']):
            return

        strong_trend = last['adx'] > self.adx_threshold
        ema_buy = (last['ema_short'] > last['ema_long']) and (last['close'] > last['ema_short'])
        ema_sell = last['ema_short'] < last['ema_long']

        if ema_buy and strong_trend:
            if not portfolio.is_long(symbol):
                portfolio.open_long(symbol, self.position_size)
        elif ema_sell:
            if portfolio.is_long(symbol):
                portfolio.close_long(symbol)