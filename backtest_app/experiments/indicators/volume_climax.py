import pandas as pd
import pandas_ta as pta

PARAMS = {
    'volume_sma_period': 10,
    'volume_std_multiplier': 2,
    'body_size_threshold': 0.5,
    'confirmation_candles': 2,
    'rsi_length': 6,
    'rsi_buy_threshold': 60,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    volume_sma_period = params.get('volume_sma_period', PARAMS['volume_sma_period'])
    volume_std_multiplier = params.get('volume_std_multiplier', PARAMS['volume_std_multiplier'])
    body_size_threshold = params.get('body_size_threshold', PARAMS['body_size_threshold'])
    confirmation_candles = params.get('confirmation_candles', PARAMS['confirmation_candles'])
    rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
    rsi_buy_threshold = params.get('rsi_buy_threshold', PARAMS['rsi_buy_threshold'])

    df['volume_sma'] = df['volume'].rolling(volume_sma_period).mean()
    df['volume_std'] = df['volume'].rolling(volume_sma_period).std()
    df['volume_threshold'] = df['volume_sma'] + (volume_std_multiplier * df['volume_std'])
    
    df['volume_spike'] = df['volume'] > df['volume_threshold']
    
    df['candle_range'] = df['high'] - df['low']
    df['candle_body'] = abs(df['close'] - df['open'])
    df['small_candle'] = df['candle_body'] < (body_size_threshold * df['candle_range'])
    
    df['climax'] = df['volume_spike'] & df['small_candle']
    
    df['climax_bullish'] = df['close'] > df['open']
    
    df['rsi'] = pta.rsi(df['close'], length=rsi_length)
    
    buy_confirmed = pd.Series([False] * len(df), index=df.index)
    
    for i in range(confirmation_candles, len(df)):
        if df['climax'].iloc[i - confirmation_candles] and df['climax_bullish'].iloc[i - confirmation_candles]:
            current_rsi = df['rsi'].iloc[i]
            recent_closes = df['close'].iloc[i - confirmation_candles + 1:i + 1]
            if len(recent_closes) >= confirmation_candles:
                higher_lows = all(recent_closes.iloc[j] > recent_closes.iloc[j - 1] for j in range(1, len(recent_closes)))
                if higher_lows and current_rsi is not None and current_rsi < rsi_buy_threshold:
                    buy_confirmed.iloc[i] = True
    
    df['buy_signal'] = buy_confirmed
    df['sell_signal'] = False

    return df