import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    df['obv'] = pta.obv(df['close'], df['volume'])
    df['obv_sma'] = df['obv'].rolling(10).mean()
    df['obv_slope'] = df['obv'].diff(5)
    
    df.iloc[:10, df.columns.get_loc('obv')] = np.nan
    df.iloc[:10, df.columns.get_loc('obv_sma')] = np.nan
    df.iloc[:10, df.columns.get_loc('obv_slope')] = np.nan
    
    df['buy_signal'] = (df['obv'] > df['obv_sma']).fillna(False)
    df['sell_signal'] = (df['obv'] < df['obv_sma']).fillna(False)

    return df
