import pandas as pd
import pandas_ta as pta

PARAMS = {
    'bollinger_length': 20,
    'bollinger_std': 2,
    'supertrend_length': 12,
    'supertrend_multiplier': 3,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    bollinger_length = params.get('bollinger_length', PARAMS['bollinger_length'])
    bollinger_std = params.get('bollinger_std', PARAMS['bollinger_std'])
    supertrend_length = params.get('supertrend_length', PARAMS['supertrend_length'])
    supertrend_multiplier = params.get('supertrend_multiplier', PARAMS['supertrend_multiplier'])

    bbands = pta.bbands(df['close'], length=bollinger_length, std=bollinger_std)
    if bbands is not None:
        df['bollinger_lower'] = bbands.iloc[:, 0]
        df['bollinger_mid'] = bbands.iloc[:, 1]
        df['bollinger_upper'] = bbands.iloc[:, 2]
    
    st = pta.supertrend(df['high'], df['low'], df['close'], length=supertrend_length, multiplier=supertrend_multiplier)
    if st is not None:
        df['supertrend'] = st.iloc[:, 0]
        df['supertrend_direction'] = st.iloc[:, 1]
    
    bollinger_buy = df['close'] < df['bollinger_lower']
    bollinger_sell = df['close'] > df['bollinger_upper']
    supertrend_bullish = df['close'] > df['supertrend']
    
    df['buy_signal'] = (bollinger_buy & supertrend_bullish).fillna(False)
    df['sell_signal'] = bollinger_sell.fillna(False)

    return df