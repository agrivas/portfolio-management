import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from utils.data_loader import load_ohlcv_data
from utils.backtest import run_backtest, plot_backtest_results
from robo_trader.strategies import get_all_strategies


def show(symbol, timeframe, start_date, end_date):
    st.title("Strategy Backtesting")

    st.header("Strategy")
    strategies = get_all_strategies()

    if st.button("Reload", key="reload_strategies"):
        st.rerun()

    selected_strategy = st.selectbox("Select", strategies)

    if selected_strategy:
        st.header("Settings")
        initial_cash = st.number_input("Initial Cash", value=10000.0, step=1000.0)
        transaction_cost = st.number_input("Fee (%)", value=0.1, step=0.05) / 100

        run_button = st.button("Run Backtest", type="primary")
    else:
        run_button = False

    if not selected_strategy:
        st.warning("Select a strategy")
    elif not run_button:
        st.info("Select a strategy above and click 'Run Backtest'")
    else:
        strategy_class = getattr(__import__('robo_trader.strategies', fromlist=[selected_strategy]), selected_strategy)

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

            with st.spinner("Running backtest..."):
                result = run_backtest(
                    strategy_class=strategy_class,
                    strategy_params={},
                    data=data,
                    symbol=symbol,
                    timeframe=timeframe,
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
                    {"Metric": "Win Rate", "Value": stats['win_rate']},
                    {"Metric": "Wins", "Value": stats['wins']},
                    {"Metric": "Losses", "Value": stats['trades'] - stats['wins']},
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