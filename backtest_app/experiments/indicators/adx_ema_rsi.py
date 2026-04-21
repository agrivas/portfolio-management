import pandas as pd
import pandas_ta as pta
import numpy as np
from scipy.signal import argrelextrema

PARAMS = {
    'ema_short': 6,
    'ema_long': 72,
    'adx_length': 12,
    'rsi_length': 48,
    'adx_threshold': 30,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    ema_short = params.get('ema_short', PARAMS['ema_short'])
    ema_long = params.get('ema_long', PARAMS['ema_long'])
    adx_length = params.get('adx_length', PARAMS['adx_length'])
    rsi_length = params.get('rsi_length', PARAMS['rsi_length'])
    adx_threshold = params.get('adx_threshold', PARAMS['adx_threshold'])

    df['sma_very_short'] = pta.ema(df['close'], length=6)
    df['sma_short'] = pta.ema(df['close'], length=ema_short)
    df['sma_long'] = pta.ema(df['close'], length=ema_long)
    
    adx = pta.adx(df['high'], df['low'], df['close'], length=adx_length)
    if adx is not None:
        df['adx_short'] = adx['ADX_' + str(adx_length)].ffill()
        df['adx_long'] = adx['ADX_48'].ffill() if 'ADX_48' in adx.columns else df['adx_short']
    
    df['rsi_short'] = pta.rsi(df['close'], length=rsi_length)
    df['rsi_long'] = pta.rsi(df['close'], length=rsi_length)
    
    df['rsi_sma_short'] = pta.rsi(df['sma_short'], length=rsi_length)
    df['rsi_sma_long'] = pta.rsi(df['sma_long'], length=rsi_length)

    def is_local_minima(series, lookback=3):
        series_diff = series.diff(periods=1)
        midpoint = lookback // 2
        average_drop = series_diff[series < 0].mean()
        average_rise = series_diff[series > 0].mean()
        conditions = [(series_diff.shift(i) < 0) for i in range(lookback-1, midpoint-1, -1)]
        conditions.extend([(series_diff.shift(i) > 0) for i in range(midpoint-1, -1, -1)])
        return pd.concat(conditions, axis=1).all(axis=1)

    def detect_deep_v_shapes(curve_series, order):
        periods = (order // 2) - 1
        depth_threshold = curve_series.diff(periods=periods).abs().mean()
        slope_threshold = 0
        minima = argrelextrema(curve_series.values, np.less, order=order)[0]
        v_shapes = pd.Series(False, index=curve_series.index)
        
        for idx in minima:
            if idx - order < 0 or idx + order >= len(curve_series):
                continue
            left_slope = (curve_series.iloc[idx] - curve_series.iloc[idx - order]) / order
            right_slope = (curve_series.iloc[idx + order] - curve_series.iloc[idx]) / order
            if left_slope < -slope_threshold and right_slope > slope_threshold:
                depth = min(curve_series.iloc[idx - order] - curve_series.iloc[idx],
                            curve_series.iloc[idx + order] - curve_series.iloc[idx])
                if depth > depth_threshold:
                    v_shapes.iloc[idx + order] = True
        
        return v_shapes

    df['sma_long_minima'] = is_local_minima(df['sma_long'], 24)
    df['sma_short_minima'] = is_local_minima(df['sma_short'], 12)
    df['v_shape'] = detect_deep_v_shapes(df['sma_long'], 6)
    
    df['strong_trend'] = df['adx_short'] > adx_threshold
    df['rsi_not_overbought'] = df['rsi_sma_long'] < 20
    
    df['sma_buy'] = (df['sma_short'] > df['sma_long']) & (df['sma_very_short'] > df['sma_short'])
    df['sma_sell'] = (df['sma_very_short'] < df['sma_long'])
    
    df['buy_signal'] = (df['sma_buy'] & df['strong_trend'] & df['rsi_not_overbought']).fillna(False)
    df['sell_signal'] = (df['sma_short'] < df['sma_long']).fillna(False)

    return df