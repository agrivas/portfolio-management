import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'fast': 12,
    'slow': 26,
    'signal': 9,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast = params.get('fast', PARAMS['fast'])
    slow = params.get('slow', PARAMS['slow'])
    signal = params.get('signal', PARAMS['signal'])

    macd = pta.macd(df['close'], fast=fast, slow=slow, signal=signal)
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 2]
        df['macd_hist'] = macd.iloc[:, 1]
        
        warmup = slow - 1
        df.iloc[:warmup, df.columns.get_loc('macd')] = np.nan
        df.iloc[:warmup, df.columns.get_loc('macd_signal')] = np.nan
        df.iloc[:warmup, df.columns.get_loc('macd_hist')] = np.nan
        
        df['macd_cross_up'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df['macd_cross_down'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        df['buy_signal'] = df['macd_cross_up'].fillna(False)
        df['sell_signal'] = df['macd_cross_down'].fillna(False)

    return df