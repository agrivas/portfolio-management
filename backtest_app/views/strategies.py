import streamlit as st
import pandas as pd
from datetime import datetime

from utils.data_loader import load_ohlcv_data
from utils.backtest import run_backtest, plot_backtest_results
from robo_trader.strategies import get_all_strategies, get_strategy_params


def show(symbol, timeframe, start_date, end_date):
    st.title("Strategy Backtesting")

    all_strategies = get_all_strategies()

    with st.sidebar:
        st.subheader("Strategy")
        selected_strategy = st.selectbox(
            "Select",
            options=all_strategies,
            key="strategy_select"
        )

        st.subheader("Settings")
        initial_cash = st.number_input("Initial Cash", value=10000.0, step=1000.0)
        transaction_cost = st.number_input("Fee (%)", value=0.4, step=0.01) / 100

        strategy_params = {}
        if selected_strategy:
            default_params = get_strategy_params(selected_strategy)
            for param_name, default_value in default_params.items():
                if isinstance(default_value, bool):
                    strategy_params[param_name] = st.checkbox(param_name, default_value, key=f"sp_{param_name}")
                elif isinstance(default_value, int):
                    strategy_params[param_name] = st.number_input(param_name, value=default_value, step=1, key=f"sp_{param_name}")
                elif isinstance(default_value, float):
                    strategy_params[param_name] = st.number_input(param_name, value=float(default_value), step=0.01, key=f"sp_{param_name}")

        if st.button("Run Backtest", type="primary"):
            if selected_strategy:
                st.session_state['backtest_ready'] = True
                st.session_state['selected_strategy_class'] = getattr(
                    __import__('robo_trader.strategies', fromlist=[selected_strategy]),
                    selected_strategy
                )
            else:
                st.warning("Select a strategy")

    if not st.session_state.get('backtest_ready', False):
        st.info("Configure settings in sidebar and click Run Backtest")
        return

    strategy_class = st.session_state.get('selected_strategy_class')
    if not strategy_class:
        return

    with st.spinner("Loading data..."):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        try:
            data = load_ohlcv_data(symbol, timeframe, start_date=start_dt, end_date=end_dt)
        except Exception as e:
            st.error(f"Error: {e}")
            return

    if data is None or data.empty:
        st.error("No data. Try different dates.")
        return

    st.success(f"Loaded {len(data):,} rows")

    with st.spinner("Running backtest..."):
        result = run_backtest(
            strategy_class=strategy_class,
            strategy_params=strategy_params,
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
        df_trade = pd.DataFrame({
            "Metric": ["Trades", "Win Rate", "Wins", "Losses"],
            "Value": [
                str(int(stats['trades'])),
                str(stats['win_rate']),
                str(int(stats['wins'])),
                str(int(stats['trades'] - stats['wins'])),
            ],
        })
        st.table(df_trade)

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