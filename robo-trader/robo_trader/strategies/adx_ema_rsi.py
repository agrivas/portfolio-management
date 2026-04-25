from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'position_size': 1.0,
    'rsi_length': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'adx_length': 14,
    'adx_threshold': 25,
    'ema_length': 50,
}


class AdxEmaRsiStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
        self.rsi_oversold = params.get('rsi_oversold', PARAMS['rsi_oversold'])
        self.rsi_overbought = params.get('rsi_overbought', PARAMS['rsi_overbought'])
        self.adx_length = params.get('adx_length', PARAMS['adx_length'])
        self.adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])
        self.ema_length = params.get('ema_length', PARAMS['ema_length'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < self.rsi_length + self.adx_length + self.ema_length:
            return

        data = prices.copy()

        rsi = pta.rsi(data['close'], length=self.rsi_length)
        data['rsi'] = rsi

        adx = pta.adx(data['high'], data['low'], data['close'], length=self.adx_length)
        data['adx'] = adx[f'ADX_{self.adx_length}']

        ema = pta.ema(data['close'], length=self.ema_length)
        data['ema'] = ema

        last = data.iloc[-1]

        if pd.isna(last['rsi']) or pd.isna(last['adx']) or pd.isna(last['ema']):
            return

        strong_trend = last['adx'] > self.adx_threshold
        rsi_buy = last['rsi'] < self.rsi_oversold
        rsi_sell = last['rsi'] > self.rsi_overbought
        ema_trend = last['close'] > last['ema']

        if rsi_buy and strong_trend and ema_trend:
            if not portfolio.is_long(symbol):
                portfolio.open_long(symbol, self.position_size)
        elif rsi_sell:
            if portfolio.is_long(symbol):
                portfolio.close_long(symbol)