import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_loader import (
    get_available_symbols,
    get_symbol_timeframes,
    get_symbol_stats,
    get_date_range_for_pair,
    load_ohlcv_data,
    AVAILABLE_TIMEFRAMES,
)
from utils.backtest import (
    discover_strategies,
    get_strategy_params,
    load_strategy_class,
    run_backtest,
    plot_backtest_results,
    format_backtest_stats,
)

st.set_page_config(page_title="Strategy Backtesting", layout="wide")

st.title("Strategy Backtesting")

# === UI CONTROLS (no data loading) ===
with st.sidebar:
    st.header("Data")

    available_symbols = get_available_symbols()
    if not available_symbols:
        st.error("No data")
    else:
        symbol = st.selectbox(
            "Symbol",
            available_symbols,
            format_func=lambda x: f"{x}"
        )

    # Step 2: Timeframe
    timeframes = get_symbol_timeframes(symbol)
    timeframe = st.selectbox(
        "Frequency",
        timeframes,
        index=timeframes.index('15m') if '15m' in timeframes else 0
    )

    # Stats
    info = get_symbol_stats(symbol, timeframe)
    if info:
        st.caption(f"📊 {info.get('rows', 0):,} rows | {info.get('size_mb', 0):.1f} MB")

    # Date range
    st.header("Date Range")
    first_dt, latest_dt = get_date_range_for_pair(symbol, timeframe)
    
    start_date = st.date_input(
        "Start",
        value=(latest_dt - timedelta(days=30)).date(),
        min_value=first_dt.date(),
        max_value=latest_dt.date()
    )
    
    end_date = st.date_input(
        "End",
        value=latest_dt.date(),
        min_value=first_dt.date(),
        max_value=latest_dt.date()
    )
    
    st.caption(f"📅 {(end_date - start_date).days} days")

    # Strategy
    st.header("Strategy")
    strategies = discover_strategies()
    st.write("")
    if st.button("Reload", key="reload_strategies"):
        st.rerun()
    
    if not strategies:
        st.info("No strategies found")
        selected_strategy = None
    else:
        selected_strategy = st.selectbox(
            "Select",
            list(strategies.keys())
        )

    if selected_strategy:
        st.header("Settings")
        initial_cash = st.number_input("Initial Cash", value=10000.0, step=1000.0)
        transaction_cost = st.number_input("Fee (%)", value=0.1, step=0.05) / 100

        strategy_params = {}
        with st.expander("Params"):
            defaults = get_strategy_params(selected_strategy)
            if defaults:
                cols = st.columns(2)
                for i, (param_name, default_value) in enumerate(defaults.items()):
                    col = cols[i % 2]
                    key = f"strat_{param_name}"
                    if isinstance(default_value, int):
                        strategy_params[param_name] = col.number_input(param_name, value=int(default_value), key=key)
                    elif isinstance(default_value, float):
                        strategy_params[param_name] = col.number_input(param_name, value=float(default_value), key=key)
                    else:
                        strategy_params[param_name] = col.text_input(param_name, value=str(default_value), key=key)
            else:
                st.caption("Default params")

        run_button = st.button("Run Backtest", type="primary")
    else:
        run_button = False
        strategy_params = {}

if not selected_strategy:
    st.warning("Select a strategy")
elif not run_button:
    st.info("👈 Configure and click 'Run Backtest'")
else:
    # === LOAD DATA (only when button clicked) ===
    with st.spinner("Loading data..."):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        try:
            data = load_ohlcv_data(symbol, timeframe, start_date=start_dt, end_date=end_dt)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    if data is None or data.empty:
        st.error("No data. Try different dates.")
    else:
        st.success(f"Loaded {len(data):,} rows")

        strategy_class = load_strategy_class(selected_strategy)

        if strategy_class is None:
            st.error(f"Could not load: {selected_strategy}")
        else:
            with st.spinner("Running backtest..."):
                result = run_backtest(
                    strategy_class=strategy_class,
                    strategy_params=strategy_params,
                    data=data,
                    initial_cash=initial_cash,
                    transaction_cost=transaction_cost,
                )

            if result.get('success'):
                stats = result['stats']

                st.subheader("Performance Comparison")

                comparison_data = [
                    {"Metric": "Return", "Strategy": f"{stats['portfolio_return']*100:+.1f}%", "Buy & Hold": f"{stats['asset_return']*100:+.1f}%"},
                    {"Metric": "Max Drawdown", "Strategy": f"{stats['portfolio_max_drawdown']*100:.1f}%", "Buy & Hold": f"{stats['asset_max_drawdown']*100:.1f}%"},
                    {"Metric": "Max Run-up", "Strategy": f"{stats['portfolio_max_runup']*100:+.1f}%", "Buy & Hold": f"{stats['asset_max_runup']*100:+.1f}%"},
                    {"Metric": "Sharpe", "Strategy": f"{stats['sharpe']:.2f}", "Buy & Hold": f"{stats['sharpe_bh']:.2f}"},
                    {"Metric": "Sortino", "Strategy": f"{stats['sortino']:.2f}", "Buy & Hold": f"{stats['sortino_bh']:.2f}"},
                ]
                st.table(pd.DataFrame(comparison_data))

                st.subheader("Trade Statistics")
                trade_data = [
                    {"Metric": "Trades", "Value": stats['trades']},
                    {"Metric": "Win Rate", "Value": f"{stats['win_rate']*100:.0f}%"},
                    {"Metric": "Wins", "Value": stats['wins']},
                    {"Metric": "Losses", "Value": stats['trades'] - stats['wins']},
                    {"Metric": "Avg Win", "Value": f"{stats['avg_win']*100:.1f}%"},
                    {"Metric": "Avg Loss", "Value": f"{stats['avg_loss']*100:.1f}%"},
                    {"Metric": "EV", "Value": f"{stats['ev']*100:.1f}%"},
                    {"Metric": "Profit Factor", "Value": f"{stats['profit_factor']:.2f}"},
                ]
                st.table(pd.DataFrame(trade_data))

                st.subheader("Portfolio Value")
                col1, col2 = st.columns(2)
                col1.metric("Initial", f"${stats['initial_value']:,.0f}")
                col2.metric("Final", f"${stats['final_value']:,.0f}")

                fig, axes = plot_backtest_results(result, figsize=(14, 8))
                st.pyplot(fig)
            else:
                st.error(f"Backtest failed: {result.get('error')}")

    with st.expander("Data"):
        st.dataframe(data.head(20))