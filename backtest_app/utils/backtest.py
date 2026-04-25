import os
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta

import pandas as pd

from robo_trader.trader import Trader
from robo_trader.feeds import KrakenCSVFeed
from robo_trader.brokers.backtest_broker import BacktestBroker
from robo_trader.strategies import get_all_strategies


def get_strategy_class(name: str):
    """Get a strategy class by name."""
    from robo_trader.strategies import __all__ as strategies
    module = __import__('robo_trader.strategies', fromlist=[name])
    return getattr(module, name, None)


def run_backtest(
    strategy_class,
    strategy_params: dict,
    data: pd.DataFrame,
    symbol: str = 'ETHUSD',
    timeframe: str = '15m',
    initial_cash: float = 10000,
    transaction_cost: float = 0.001,
    trailing_stop_penalty_relief: float = 0.75,
) -> dict:
    data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'kraken')

    feed = KrakenCSVFeed(data_dir=data_dir, interval=timeframe)
    strategy = strategy_class(strategy_params)
    backtest_broker = BacktestBroker(
        transaction_cost=transaction_cost,
        trailing_stop_penalty_relief=trailing_stop_penalty_relief
    )
    trader = Trader(
        symbol=symbol,
        initial_cash=initial_cash,
        feed=feed,
        strategy=strategy,
        broker=backtest_broker
    )

    if data is not None and len(data) > 0:
        start_date = data.index[0]
        end_date = data.index[-1]
    else:
        end_dt = datetime(2025, 12, 31)
        start_dt = end_dt - timedelta(days=30)
        start_date = pd.Timestamp(start_dt, tz='UTC')
        end_date = pd.Timestamp(end_dt, tz='UTC')

    result = trader.backtest(
        start_date=start_date,
        end_date=end_date,
        transaction_cost=transaction_cost,
        trailing_stop_penalty_relief=trailing_stop_penalty_relief
    )

    if result is None:
        return {
            'success': False,
            'error': 'No data returned from backtest',
        }

    performance = result.calculate_performance()

    return {
        'success': True,
        'stats': {
            'initial_value': performance['initial_value'],
            'final_value': performance['final_value'],
            'win_rate': performance['win_rate'],
            'wins': performance['wins'],
            'trades': performance['trades'],
            'portfolio_return': performance['portfolio_return'],
            'asset_return': performance['asset_return'],
            'portfolio_max_drawdown': performance['portfolio_max_drawdown'],
            'asset_max_drawdown': performance['asset_max_drawdown'],
            'sharpe': performance['sharpe'],
            'sortino': performance['sortino'],
            'sharpe_bh': performance['sharpe_bh'],
            'sortino_bh': performance['sortino_bh'],
            'ev': performance['ev'],
            'avg_win': performance['avg_win'],
            'avg_loss': performance['avg_loss'],
            'profit_factor': performance['profit_factor'],
            'portfolio_max_runup': performance['portfolio_max_runup'],
            'asset_max_runup': performance['asset_max_runup'],
        },
        'performance': performance['performance'],
    }


def plot_backtest_results(result: dict, figsize=(14, 10)):
    import matplotlib.pyplot as plt

    if not result.get('success', False):
        print(f"Backtest failed: {result.get('error', 'Unknown error')}")
        return None

    df = result['performance']

    fig, axes = plt.subplots(3, 1, figsize=figsize, gridspec_kw={'height_ratios': [2, 1, 1]})

    ax1 = axes[0]
    ax1.plot(df.index, df['asset_price'], color='blue', label='Asset Price', alpha=0.7)

    open_long = df[df['open_long'] == True]
    if len(open_long) > 0:
        ax1.scatter(open_long.index, open_long['asset_price'], color='green', marker='^', s=150, label='Open Long')

    close_long = df[df['close_long'] == True]
    if len(close_long) > 0:
        ax1.scatter(close_long.index, close_long['asset_price'], color='red', marker='v', s=150, label='Close Long')

    ax1.set_title('Trading Signals')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    ax2.plot(df.index, df['portfolio_value'], color='purple', label='Portfolio Value')
    ax2.set_title('Portfolio Value')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[2]
    ax3.plot(df.index, df['portfolio_return'], color='green', label='Strategy Return')
    ax3.plot(df.index, df['buy_and_hold_return'], color='orange', label='Buy & Hold Return')
    ax3.set_title('Return vs Buy & Hold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    plt.tight_layout()
    return fig, axes


def format_backtest_stats(stats: dict) -> str:
    lines = [
        "=== Backtest Results ===",
        f"Initial Value: ${stats['initial_value']:,.2f}",
        f"Final Value: ${stats['final_value']:,.2f}",
        f"Strategy Return: {stats['portfolio_return']*100:.2f}%",
        f"Buy & Hold Return: {stats['asset_return']*100:.2f}%",
        f"Win Rate: {stats['win_rate']*100:.1f}% ({stats['wins']}/{stats['trades']} trades)",
        f"Max Drawdown (Strategy): {stats['portfolio_max_drawdown']*100:.2f}%",
        f"Max Drawdown (Buy & Hold): {stats['asset_max_drawdown']*100:.2f}%",
    ]
    return '\n'.join(lines)