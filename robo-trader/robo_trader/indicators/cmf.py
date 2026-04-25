import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'length': 20,
    'cmf_oversold': -0.1,
    'cmf_overbought': 0.1,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    cmf_oversold = params.get('cmf_oversold', PARAMS['cmf_oversold'])
    cmf_overbought = params.get('cmf_overbought', PARAMS['cmf_overbought'])

    df['cmf'] = pta.cmf(df['high'], df['low'], df['close'], df['volume'], length=length)
    if length > 0:
        df.iloc[:length, df.columns.get_loc('cmf')] = np.nan
    
    df['buy_signal'] = (df['cmf'] > cmf_overbought).fillna(False)
    df['sell_signal'] = (df['cmf'] < cmf_oversold).fillna(False)

    return df