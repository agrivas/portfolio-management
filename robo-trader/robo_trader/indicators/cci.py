import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'length': 168,
    'oversold_threshold': -250,
    'overbought_threshold': 250,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    oversold_threshold = params.get('oversold_threshold', PARAMS['oversold_threshold'])
    overbought_threshold = params.get('overbought_threshold', PARAMS['overbought_threshold'])

    df['cci'] = pta.cci(df['high'], df['low'], df['close'], length=length)
    if length > 0:
        df.iloc[:length, df.columns.get_loc('cci')] = np.nan
    
    df['cci_oversold'] = df['cci'] < oversold_threshold
    df['cci_overbought'] = df['cci'] > overbought_threshold
    
    df['buy_signal'] = df['cci_oversold'].fillna(False)
    df['sell_signal'] = df['cci_overbought'].fillna(False)

    return df