import pandas as pd
import pandas_ta as pta

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
    if adx is not None and 'ADX_' + str(length) in adx.columns:
        df['adx'] = adx['ADX_' + str(length)].ffill()
        df['adx_neg'] = adx['ADXN_' + str(length)].ffill()
        df['adx_pos'] = adx['ADXP_' + str(length)].ffill()
        
        df['strong_trend'] = (df['adx'] > strong_threshold).fillna(False)
        df['weak_trend'] = (df['adx'] < weak_threshold).fillna(False)
        
        df['buy_signal'] = df['strong_trend']
        df['sell_signal'] = df['weak_trend']
    else:
        df['buy_signal'] = False
        df['sell_signal'] = False

    return df