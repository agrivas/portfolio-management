import pandas as pd
import pandas_ta as pta

PARAMS = {
    'rsi_length': 14,
    'rsi_oversold': 30,
    'lookback_period': 20,
    'confirmation_bars': 3,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
    rsi_oversold = params.get('rsi_oversold', PARAMS['rsi_oversold'])
    lookback_period = params.get('lookback_period', PARAMS['lookback_period'])
    confirmation_bars = params.get('confirmation_bars', PARAMS['confirmation_bars'])

    df['rsi'] = pta.rsi(df['close'], length=rsi_length)

    df['lowest_low'] = df['close'].rolling(lookback_period).min()
    df['above_lowest'] = df['close'] > df['lowest_low']

    confirmation_cols = [df['above_lowest'].shift(i).fillna(False) for i in range(confirmation_bars)]
    df['confirmed_recovery'] = pd.concat(confirmation_cols, axis=1).all(axis=1)

    df['rsi_was_oversold'] = df['rsi'].rolling(5).max().shift(1) < rsi_oversold
    df['rsi_recovering'] = df['rsi'] > df['rsi'].shift(1)

    df['v_recovery'] = df['confirmed_recovery'] & df['rsi_was_oversold'] & df['rsi_recovering']

    df['v_recovery'] = df['v_recovery'].fillna(False)

    df['buy_signal'] = df['v_recovery']
    df['sell_signal'] = False

    return df