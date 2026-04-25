import pandas as pd
import pandas_ta as pta

PARAMS = {
    'rsi_short': 6,
    'rsi_long': 28,
    'sma_short': 6,
    'sma_long': 168,
    'adx_length': 14,
    'adx_threshold': 30,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    rsi_short = params.get('rsi_short', PARAMS['rsi_short'])
    rsi_long = params.get('rsi_long', PARAMS['rsi_long'])
    sma_short = params.get('sma_short', PARAMS['sma_short'])
    sma_long = params.get('sma_long', PARAMS['sma_long'])
    adx_length = params.get('adx_length', PARAMS['adx_length'])
    adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])

    df['rsi_short'] = pta.rsi(df['close'], length=rsi_short)
    df['rsi_long'] = pta.rsi(df['close'], length=rsi_long)
    
    df['sma_short'] = pta.sma(df['close'], length=sma_short)
    df['sma_long'] = pta.sma(df['close'], length=sma_long)
    
    adx = pta.adx(df['high'], df['low'], df['close'], length=adx_length)
    if adx is not None and 'ADX_' + str(adx_length) in adx.columns:
        df['adx'] = adx['ADX_' + str(adx_length)].ffill()
    else:
        df['adx'] = pd.Series([None] * len(df), index=df.index)
    
    df['rsi_short_oversold'] = (df['rsi_short'] < 10).fillna(False)
    df['rsi_long_not_overbought'] = (df['rsi_long'] < 40).fillna(False)
    df['sma_short_over_long'] = df['sma_short'] > df['sma_long']
    df['strong_trend'] = (df['adx'] > adx_threshold).fillna(False)
    
    df['buy_signal'] = df['rsi_short_oversold'] & df['rsi_long_not_overbought']
    df['sell_signal'] = False

    return df