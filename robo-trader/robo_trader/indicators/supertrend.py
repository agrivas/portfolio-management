import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'length': 12,
    'multiplier': 3,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    multiplier = params.get('multiplier', PARAMS['multiplier'])

    st = pta.supertrend(df['high'], df['low'], df['close'], length=length, multiplier=multiplier)
    if st is not None:
        df['supertrend'] = st.iloc[:, 0]
        df['supertrend_direction'] = st.iloc[:, 2]
        
        df.iloc[:length, df.columns.get_loc('supertrend')] = np.nan
        df.iloc[:length, df.columns.get_loc('supertrend_direction')] = np.nan
        
        df['buy_signal'] = (df['close'] > df['supertrend']).fillna(False)
        df['sell_signal'] = (df['close'] < df['supertrend']).fillna(False)
    else:
        df['buy_signal'] = False
        df['sell_signal'] = False

    return df