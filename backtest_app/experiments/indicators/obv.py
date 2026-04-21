import pandas as pd
import pandas_ta as pta

PARAMS = {}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    df['obv'] = pta.obv(df['close'], df['volume'])
    
    df['obv_sma'] = df['obv'].ta.sma(length=10)
    df['obv_slope'] = df['obv'].diff(5)
    
    df['buy_signal'] = (df['obv'] > df['obv_sma']).fillna(False)
    df['sell_signal'] = (df['obv'] < df['obv_sma']).fillna(False)

    return df
