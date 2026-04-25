import pandas as pd
import pandas_ta as pta
import numpy as np

PARAMS = {
    'length': 20,
    'std': 2,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    length = params.get('length', PARAMS['length'])
    std = params.get('std', PARAMS['std'])

    bbands = pta.bbands(df['close'], length=length, std=std)
    if bbands is not None:
        df['bollinger_lower'] = bbands.iloc[:, 0]
        df['bollinger_mid'] = bbands.iloc[:, 1]
        df['bollinger_upper'] = bbands.iloc[:, 2]
        
        df.iloc[:length, df.columns.get_loc('bollinger_lower')] = np.nan
        df.iloc[:length, df.columns.get_loc('bollinger_mid')] = np.nan
        df.iloc[:length, df.columns.get_loc('bollinger_upper')] = np.nan
    
    df['buy_signal'] = (df['close'] < df['bollinger_lower']).fillna(False)
    df['sell_signal'] = (df['close'] > df['bollinger_upper']).fillna(False)

    return df