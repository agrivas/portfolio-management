import os
import importlib.util
from typing import Callable, Dict, List, Any, Optional

import pandas as pd
import numpy as np


EXPERIMENTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'experiments', 'indicators')


def discover_indicators() -> Dict[str, str]:
    indicators = {}
    if not os.path.exists(EXPERIMENTS_DIR):
        return indicators

    for filename in os.listdir(EXPERIMENTS_DIR):
        if filename.endswith('.py') and not filename.startswith('_'):
            name = filename[:-3]
            indicators[name] = filename
    return indicators


def load_indicator(name: str) -> Optional[Callable]:
    filepath = os.path.join(EXPERIMENTS_DIR, f"{name}.py")
    if not os.path.exists(filepath):
        return None

    spec = importlib.util.spec_from_file_location(name, filepath)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error loading indicator {name}: {e}")
        return None

    return getattr(module, 'run', None)


def run_indicator(name: str, df: pd.DataFrame, params: dict) -> pd.DataFrame:
    func = load_indicator(name)
    if func is None:
        return df

    try:
        result = func(df, params)
        if result is not None:
            return result
    except Exception as e:
        print(f"Error running indicator {name}: {e}")

    return df


def get_default_params(name: str) -> dict:
    filepath = os.path.join(EXPERIMENTS_DIR, f"{name}.py")
    if not os.path.exists(filepath):
        return {}

    spec = importlib.util.spec_from_file_location(name, filepath)
    if spec is None or spec.loader is None:
        return {}

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return {}

    return getattr(module, 'PARAMS', {})


DISPLAY_PANEL_OPTIONS = [
    'MACD',
    'RSI', 
    'CCI',
    'ADX',
    'MFI',
    'Bollinger',
    'Supertrend',
    'ATR',
    'Moving Averages',
]


def get_signal_columns(df: pd.DataFrame) -> tuple:
    buy_columns = [col for col in df.columns if col == 'buy_signal']
    sell_columns = [col for col in df.columns if col == 'sell_signal']
    return buy_columns, sell_columns


def build_panels(df: pd.DataFrame, display_panels: List[str]) -> List[Dict[str, Any]]:
    panels = []
    cols = df.columns

    buy_cols, sell_cols = get_signal_columns(df)
    markers = {}
    for col in buy_cols:
        markers[col] = 'green'
    for col in sell_cols:
        markers[col] = 'red'

    panels.append({
        'type': 'price',
        'title': 'Price',
        'markers': markers,
    })

    if 'MACD' in display_panels and 'macd' in cols:
        macd_cols = [c for c in ['macd', 'macd_signal', 'macd_hist'] if c in cols]
        if macd_cols:
            panels.append({
                'type': 'line',
                'columns': macd_cols,
                'title': 'MACD',
            })

    if 'RSI' in display_panels and 'rsi' in cols:
        panels.append({
            'type': 'oscillator',
            'column': 'rsi',
            'title': 'RSI',
            'lower': 30,
            'upper': 70,
        })

    if 'CCI' in display_panels and 'cci' in cols:
        panels.append({
            'type': 'oscillator',
            'column': 'cci',
            'title': 'CCI',
            'lower': -250,
            'upper': 250,
        })

    if 'ADX' in display_panels and 'adx' in cols:
        panels.append({
            'type': 'oscillator',
            'column': 'adx',
            'title': 'ADX',
            'lower': 0,
            'upper': 25,
        })

    if 'MFI' in display_panels and 'mfi' in cols:
        panels.append({
            'type': 'oscillator',
            'column': 'mfi',
            'title': 'MFI',
            'lower': 20,
            'upper': 80,
        })

    if 'Bollinger' in display_panels:
        bollinger_cols = [c for c in ['bollinger_mid', 'bollinger_upper', 'bollinger_lower'] if c in cols]
        if bollinger_cols:
            panels.append({
                'type': 'line',
                'columns': bollinger_cols,
                'title': 'Bollinger Bands',
            })

    if 'Supertrend' in display_panels and 'supertrend' in cols:
        panels.append({
            'type': 'line',
            'columns': ['supertrend'],
            'title': 'Supertrend',
        })

    if 'ATR' in display_panels and 'atr' in cols:
        panels.append({
            'type': 'line',
            'columns': ['atr'],
            'title': 'ATR',
        })

    if 'Moving Averages' in display_panels:
        ema_cols = [c for c in cols if c.startswith('ema_') or c.startswith('sma_')]
        if len(ema_cols) > 2:
            ema_cols = ema_cols[:2]
        if ema_cols:
            panels.append({
                'type': 'line',
                'columns': ema_cols,
                'title': 'Moving Averages',
            })

    return panels


def plot_price_with_indicators(
    df: pd.DataFrame,
    indicators: List[str],
    ax=None,
    figsize=(12, 6),
):
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_fig = True
    else:
        created_fig = False

    ax.plot(df.index, df['close'], label='Close', color='blue', alpha=0.7)

    for ind_name in indicators:
        if ind_name in df.columns:
            ax.plot(df.index, df[ind_name], label=ind_name, alpha=0.7)

    ax.legend()
    ax.set_title('Price with Indicators')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')

    if created_fig:
        plt.tight_layout()

    return ax


def plot_multi_panel(
    df: pd.DataFrame,
    panels: List[Dict[str, Any]],
    figsize=(14, 10),
):
    import matplotlib.pyplot as plt

    n_panels = len(panels)
    fig, axes = plt.subplots(n_panels, 1, figsize=figsize, sharex=True)

    if n_panels == 1:
        axes = [axes]

    for i, panel in enumerate(panels):
        ax = axes[i]
        panel_type = panel.get('type', 'line')

        if panel_type == 'price':
            ax.plot(df.index, df['close'], label='Close', color='blue', alpha=0.7)
            if 'markers' in panel:
                for marker_name, color in panel['markers'].items():
                    if marker_name in df.columns:
                        mask = df[marker_name] == True
                        marker = '^' if 'green' in str(color) else 'v'
                        ax.scatter(
                            df.index[mask],
                            df.loc[mask, 'close'],
                            color=color,
                            marker=marker,
                            s=100,
                            label=marker_name,
                        )
            ax.legend()

        elif panel_type == 'line':
            title = panel.get('title', '')
            for col in panel.get('columns', []):
                if col in df.columns:
                    ax.plot(df.index, df[col], label=col, alpha=0.7)
            if title in ['MACD', 'Bollinger Bands', 'Moving Averages', 'Supertrend', 'ATR']:
                ax.plot(df.index, df['close'], label='Close', color='blue', alpha=0.3, linewidth=0.5)
            ax.legend()

        elif panel_type == 'histogram':
            col = panel.get('column')
            if col and col in df.columns:
                ax.bar(df.index, df[col], color=panel.get('color', 'gray'), alpha=0.5)
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        elif panel_type == 'oscillator':
            col = panel.get('column')
            if col and col in df.columns:
                ax.plot(df.index, df[col], label=col, color='purple')
                if 'lower' in panel and panel['lower'] is not None:
                    ax.axhline(y=panel['lower'], color='green', linestyle='--', alpha=0.5)
                if 'upper' in panel and panel['upper'] is not None:
                    ax.axhline(y=panel['upper'], color='red', linestyle='--', alpha=0.5)
            ax.legend()

        ax.set_title(panel.get('title', ''))
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig, axes


def plot_candlestick(df: pd.DataFrame, ax=None, figsize=(12, 6)):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        created_fig = True
    else:
        created_fig = False

    for idx, (date, row) in enumerate(df.iterrows()):
        color = 'green' if row['close'] >= row['open'] else 'red'
        ax.plot([date, date], [row['low'], row['high']], color=color, linewidth=1)
        body_height = abs(row['close'] - row['open'])
        body_bottom = min(row['open'], row['close'])
        ax.fill_between([date - pd.Timedelta(minutes=30), date + pd.Timedelta(minutes=30)],
                       body_bottom, body_bottom + body_height, color=color, alpha=0.5)

    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.grid(True, alpha=0.3)

    if created_fig:
        plt.tight_layout()

    return ax