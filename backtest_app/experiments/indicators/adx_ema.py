import pandas as pd
import pandas_ta as pta

PARAMS = {
    'adx_length': 12,
    'adx_threshold': 40,
    'ema_short': 6,
    'ema_long': 120,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    adx_length = params.get('adx_length', PARAMS['adx_length'])
    adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])
    ema_short = params.get('ema_short', PARAMS['ema_short'])
    ema_long = params.get('ema_long', PARAMS['ema_long'])

    adx = pta.adx(df['high'], df['low'], df['close'], length=adx_length)
    if adx is not None and 'ADX_' + str(adx_length) in adx.columns:
        df['adx'] = adx['ADX_' + str(adx_length)].fillna(0)
    else:
        df['adx'] = 0.0
    
    ema_s = pta.ema(df['close'], length=ema_short)
    if ema_s is not None:
        df['ema_short'] = ema_s.fillna(0)
    else:
        df['ema_short'] = df['close']
    
    ema_l = pta.ema(df['close'], length=ema_long)
    if ema_l is not None:
        df['ema_long'] = ema_l.fillna(0)
    else:
        df['ema_long'] = df['close']
    
    df['strong_trend'] = (df['adx'] > adx_threshold)
    df['ema_buy'] = (df['ema_short'] > df['ema_long']) & (df['close'] > df['ema_short'])
    
    df['buy_signal'] = df['strong_trend'] & df['ema_buy']
    df['sell_signal'] = df['ema_short'] < df['ema_long']

    return df