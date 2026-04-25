import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'length': 14,
    'strong_threshold': 25,
    'weak_threshold': 20,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    strong_threshold = params.get('strong_threshold', PARAMS['strong_threshold'])
    weak_threshold = params.get('weak_threshold', PARAMS['weak_threshold'])

    adx = pta.adx(df['high'], df['low'], df['close'], length=length)
    adx_col = 'ADX_' + str(length)
    adxn_col = 'ADXN_' + str(length)
    adxp_col = 'ADXP_' + str(length)
    
    if adx is not None and adx_col in adx.columns:
        df['adx'] = adx[adx_col].ffill()
        df['adx_neg'] = adx[adxn_col].ffill() if adxn_col in adx.columns else adx[adx_col] * 0
        df['adx_pos'] = adx[adxp_col].ffill() if adxp_col in adx.columns else adx[adx_col] * 0
        
        warmup = length - 1
        df.iloc[:warmup, df.columns.get_loc('adx')] = np.nan
        df.iloc[:warmup, df.columns.get_loc('adx_neg')] = np.nan
        df.iloc[:warmup, df.columns.get_loc('adx_pos')] = np.nan
        
        df['strong_trend'] = (df['adx'] > strong_threshold).fillna(False)
        df['weak_trend'] = (df['adx'] < weak_threshold).fillna(False)
        
        df['buy_signal'] = df['strong_trend']
        df['sell_signal'] = df['weak_trend']
    else:
        df['buy_signal'] = False
        df['sell_signal'] = False

    return df