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
    'take_profit': 0.10,
    'cci_length': 72,
    'cci_threshold': 120,
    'sma_length_short': 6,
    'sma_length_long': 72,
    'adx_length': 24,
    'adx_threshold': 40,
}


class AdxSmaCciStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.stop_loss = params.get('stop_loss', PARAMS['stop_loss'])
        self.take_profit = params.get('take_profit', PARAMS['take_profit'])
        self.cci_length = params.get('cci_length', PARAMS['cci_length'])
        self.cci_threshold = params.get('cci_threshold', PARAMS['cci_threshold'])
        self.sma_length_short = params.get('sma_length_short', PARAMS['sma_length_short'])
        self.sma_length_long = params.get('sma_length_long', PARAMS['sma_length_long'])
        self.adx_length = params.get('adx_length', PARAMS['adx_length'])
        self.adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < self.adx_length + self.cci_length:
            return

        data = prices.copy()

        data['cci'] = pta.cci(data['high'], data['low'], data['close'], length=self.cci_length)
        data['sma_short'] = pta.sma(data['close'], length=self.sma_length_short)
        data['sma_long'] = pta.sma(data['close'], length=self.sma_length_long)
        adx = pta.adx(data['high'], data['low'], data['close'], length=self.adx_length)
        data['adx'] = adx[f'ADX_{self.adx_length}']

        last = data.iloc[-1]

        if pd.isna(last['adx']) or pd.isna(last['cci']) or pd.isna(last['sma_short']):
            return

        cci_bullish = last['cci'] < self.cci_threshold
        sma_buy = (last['sma_short'] > last['sma_long']) and (last['close'] > last['sma_short'])
        strong_trend = last['adx'] > self.adx_threshold

        if cci_bullish and sma_buy and strong_trend:
            portfolio.open_long(symbol, self.position_size, None, self.take_profit, self.stop_loss)