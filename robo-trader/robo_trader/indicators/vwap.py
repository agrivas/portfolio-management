import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'anchor': 'D',
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    anchor = params.get('anchor', PARAMS['anchor'])

    df['vwap'] = pta.vwap(df['high'], df['low'], df['close'], df['volume'], anchor=anchor)
    
    df['buy_signal'] = (df['close'] > df['vwap']).fillna(False)
    df['sell_signal'] = (df['close'] < df['vwap']).fillna(False)

    return df