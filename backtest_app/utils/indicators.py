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
                        ax.scatter(
                            df.index[mask],
                            df.loc[mask, 'close'],
                            color=color,
                            marker='^',
                            s=100,
                            label=marker_name,
                        )
            ax.legend()

        elif panel_type == 'line':
            for col in panel.get('columns', []):
                if col in df.columns:
                    ax.plot(df.index, df[col], label=col, alpha=0.7)
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
                if 'lower' in panel:
                    ax.axhline(y=panel['lower'], color='green', linestyle='--', alpha=0.5)
                if 'upper' in panel:
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