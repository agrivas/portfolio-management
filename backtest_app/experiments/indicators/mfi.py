import pandas as pd
import pandas_ta as pta

PARAMS = {
    'length': 72,
    'oversold': 20,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    oversold = params.get('oversold', PARAMS['oversold'])

    df['mfi'] = pta.mfi(df['high'], df['low'], df['close'], df['volume'], length=length)
    
    df['mfi_oversold'] = df['mfi'] < oversold
    df['mfi_overbought'] = df['mfi'] > (100 - oversold)
    
    df['buy_signal'] = df['mfi_oversold'].fillna(False)
    df['sell_signal'] = df['mfi_overbought'].fillna(False)

    return df