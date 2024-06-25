from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
from dataclasses import dataclass
import pandas as pd
import pandas_ta as pta
import ta

@dataclass
class WtCciStAdxSettings:
    wavetrend_overbought_threshold: float = 60
    wavetrend_oversold_threshold: float = -60
    cci_overbought_threshold: float = 100
    cci_oversold_threshold: float = -100
    adx_threshold: float = 25
    supertrend_length: int = 9
    supertrend_multiplier: float = 3.0
    cci_window: int = 12
    adx_window: int = 12
    position_size:float = 0.25
    trailing_stop:float = 0.01

class WtCciStAdxStrategy(Strategy):
    def __init__(self, settings: WtCciStAdxSettings):
        super().__init__()
        self.settings = settings

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        # Make a copy of prices
        data = prices.copy()

        # Calculate WaveTrend
        data['wavetrend'] = self._calculate_wavetrend(data)
        data['wavetrend_overbought'] = data['wavetrend'] > self.settings.wavetrend_overbought_threshold
        data['wavetrend_oversold'] = data['wavetrend'] < self.settings.wavetrend_oversold_threshold

        # Calculate SuperTrend
        supertrend = pta.supertrend(data['high'], data['low'], data['close'], 
                                    length=self.settings.supertrend_length, 
                                    multiplier=self.settings.supertrend_multiplier)
        data['supertrend'] = supertrend[f'SUPERT_{self.settings.supertrend_length}_{self.settings.supertrend_multiplier}']
        data['supertrend_uptrend_approx'] = data['close'] - data['supertrend'] > 0

        # Calculate CCI
        data['cci'] = ta.trend.cci(data['high'], data['low'], data['close'], 
                                   window=self.settings.cci_window)

        # Calculate ADX
        data['adx'] = ta.trend.adx(data['high'], data['low'], data['close'], 
                                   window=self.settings.adx_window)

        # Generate long entry signal
        data['long_entry'] = ((data['wavetrend_oversold']) | 
                              (data['cci'] < self.settings.cci_oversold_threshold)) & \
                             (data['supertrend_uptrend_approx']) & \
                             (data['adx'] > self.settings.adx_threshold)

        # Get the last price point
        last_price_point = data.iloc[-1]

        # Check for long entry signal
        if last_price_point['long_entry']:
            portfolio.open_long(symbol, self.settings.position_size, self.settings.trailing_stop)

    def _calculate_wavetrend(self, data, n1=10, n2=21):
        ap = (data['high'] + data['low'] + data['close']) / 3
        esa = ap.ewm(span=n1, adjust=False).mean()
        d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
        ci = (ap - esa) / (0.015 * d)
        tci = ci.ewm(span=n2, adjust=False).mean()
        return tci