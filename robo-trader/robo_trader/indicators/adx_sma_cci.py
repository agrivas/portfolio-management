import pandas as pd
import pandas_ta as pta

PARAMS = {
    'cci_length': 24,
    'cci_threshold': -300,
    'sma_short': 6,
    'sma_long': 60,
    'adx_length': 24,
    'adx_threshold': 20,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    cci_length = params.get('cci_length', PARAMS['cci_length'])
    cci_threshold = params.get('cci_threshold', PARAMS['cci_threshold'])
    sma_short = params.get('sma_short', PARAMS['sma_short'])
    sma_long = params.get('sma_long', PARAMS['sma_long'])
    adx_length = params.get('adx_length', PARAMS['adx_length'])
    adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])

    df['cci'] = pta.cci(df['high'], df['low'], df['close'], length=cci_length)
    df['sma_short'] = pta.sma(df['close'], length=sma_short)
    df['sma_long'] = pta.sma(df['close'], length=sma_long)
    
    adx = pta.adx(df['high'], df['low'], df['close'], length=adx_length)
    if adx is not None and 'ADX_' + str(adx_length) in adx.columns:
        df['adx'] = adx['ADX_' + str(adx_length)].ffill()
    else:
        df['adx'] = pd.Series([None] * len(df), index=df.index)
    
    df['cci_bullish'] = (df['cci'] < cci_threshold).fillna(False)
    df['sma_buy'] = (df['sma_short'] > df['sma_long']) & (df['close'] > df['sma_short'])
    df['strong_trend'] = (df['adx'] > adx_threshold).fillna(False)
    
    df['buy_signal'] = (df['cci_bullish'] & df['sma_buy'] & df['strong_trend'])
    df['sell_signal'] = False

    return df