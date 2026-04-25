import pandas as pd
import pandas_ta as pta

PARAMS = {
    'window': 48,
    'oversold': 30,
    'overbought': 70,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    window = params.get('window', PARAMS['window'])
    oversold = params.get('oversold', PARAMS['oversold'])
    overbought = params.get('overbought', PARAMS['overbought'])

    df['rsi'] = pta.rsi(df['close'], length=window)
    
    df['rsi_oversold'] = df['rsi'] < oversold
    df['rsi_overbought'] = df['rsi'] > overbought
    
    df['buy_signal'] = df['rsi_oversold'].fillna(False)
    df['sell_signal'] = df['rsi_overbought'].fillna(False)

    return df