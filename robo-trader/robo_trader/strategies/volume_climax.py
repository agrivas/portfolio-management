from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'position_size': 1.0,
    'stop_loss': 0.05,
    'take_profit': 0.10,
    'volume_sma_period': 10,
    'volume_std_multiplier': 2,
    'body_size_threshold': 0.5,
    'confirmation_candles': 2,
    'rsi_length': 6,
    'rsi_buy_threshold': 60,
}


class VolumeClimaxStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        self.stop_loss = params.get('stop_loss', PARAMS['stop_loss'])
        self.take_profit = params.get('take_profit', PARAMS['take_profit'])
        self.volume_sma_period = params.get('volume_sma_period', PARAMS['volume_sma_period'])
        self.volume_std_multiplier = params.get('volume_std_multiplier', PARAMS['volume_std_multiplier'])
        self.body_size_threshold = params.get('body_size_threshold', PARAMS['body_size_threshold'])
        self.confirmation_candles = params.get('confirmation_candles', PARAMS['confirmation_candles'])
        self.rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
        self.rsi_buy_threshold = params.get('rsi_buy_threshold', PARAMS['rsi_buy_threshold'])

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        if len(prices) < self.volume_sma_period + self.confirmation_candles:
            return

        data = prices.copy()

        data['volume_sma'] = data['volume'].rolling(self.volume_sma_period).mean()
        data['volume_std'] = data['volume'].rolling(self.volume_sma_period).std()
        data['volume_threshold'] = data['volume_sma'] + (self.volume_std_multiplier * data['volume_std'])

        data['volume_spike'] = data['volume'] > data['volume_threshold']

        data['candle_range'] = data['high'] - data['low']
        data['candle_body'] = abs(data['close'] - data['open'])
        data['small_candle'] = data['candle_body'] < (self.body_size_threshold * data['candle_range'])

        data['climax'] = data['volume_spike'] & data['small_candle']
        data['climax_bullish'] = data['close'] > data['open']

        data['rsi'] = pta.rsi(data['close'], length=self.rsi_length)

        i = len(data) - 1
        if data['climax'].iloc[i - self.confirmation_candles] and data['climax_bullish'].iloc[i - self.confirmation_candles]:
            current_rsi = data['rsi'].iloc[i]
            recent_closes = data['close'].iloc[i - self.confirmation_candles + 1:i + 1]
            if len(recent_closes) >= self.confirmation_candles:
                higher_lows = all(recent_closes.iloc[j] > recent_closes.iloc[j - 1] for j in range(1, len(recent_closes)))
                if higher_lows and current_rsi is not None and current_rsi < self.rsi_buy_threshold:
                    portfolio.open_long(
                        symbol,
                        self.position_size,
                        None,
                        self.take_profit,
                        self.stop_loss
                    )