import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from utils.data_loader import load_ohlcv_data
from robo_trader.indicators import get_all_indicators, get_indicator_params

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def derive_display_name(runner_name):
    return runner_name.replace('run_', '').replace('_', ' ').title()


def discover_sub_panels(df):
    sub_panels = []
    cols = df.columns
    
    if 'rsi' in cols:
        sub_panels.append(('rsi', {'title': 'RSI', 'lower': 30, 'upper': 70}))
    
    if 'macd' in cols:
        sub_panels.append(('macd', {'title': 'MACD'}))
    
    if 'cci' in cols:
        sub_panels.append(('cci', {'title': 'CCI', 'lower': -250, 'upper': 250}))
    
    if 'adx' in cols:
        sub_panels.append(('adx', {'title': 'ADX', 'lower': None, 'upper': 25}))
    
    if 'mfi' in cols:
        sub_panels.append(('mfi', {'title': 'MFI', 'lower': 20, 'upper': 80}))
    
    if 'obv' in cols:
        sub_panels.append(('obv', {'title': 'OBV'}))
    
    if any(col.startswith('bollinger') for col in cols):
        sub_panels.append(('bollinger', {'title': 'Bollinger'}))
    
    if 'supertrend' in cols:
        sub_panels.append(('supertrend', {'title': 'Supertrend'}))
    
    if 'cmf' in cols:
        sub_panels.append(('cmf', {'title': 'CMF', 'lower': -0.1, 'upper': 0.1}))
    
    if 'vwap' in cols:
        sub_panels.append(('vwap', {'title': 'VWAP'}))
    
    if any(col.startswith(('sma_', 'ema_')) for col in cols):
        sub_panels.append(('ma', {'title': 'Moving Averages'}))
    
    return sub_panels


def render_sub_panel(ax, panel_name, df):
    if panel_name == 'rsi':
        ax.plot(df.index, df['rsi'], label='RSI', color='purple')
        ax.axhline(30, color='green', linestyle='--', alpha=0.5)
        ax.axhline(70, color='red', linestyle='--', alpha=0.5)
    elif panel_name == 'macd':
        if 'macd' in df.columns:
            ax.plot(df.index, df['macd'], label='MACD', color='blue')
        if 'macd_signal' in df.columns:
            ax.plot(df.index, df['macd_signal'], label='Signal', color='orange')
        if 'macd_hist' in df.columns:
            ax.bar(df.index, df['macd_hist'], label='Hist', color='gray', alpha=0.5)
    elif panel_name == 'cci':
        ax.plot(df.index, df['cci'], label='CCI', color='purple')
        ax.axhline(-250, color='green', linestyle='--', alpha=0.5)
        ax.axhline(250, color='red', linestyle='--', alpha=0.5)
    elif panel_name == 'adx':
        ax.plot(df.index, df['adx'], label='ADX', color='purple')
        ax.axhline(25, color='red', linestyle='--', alpha=0.5)
    elif panel_name == 'mfi':
        ax.plot(df.index, df['mfi'], label='MFI', color='purple')
        ax.axhline(20, color='green', linestyle='--', alpha=0.5)
        ax.axhline(80, color='red', linestyle='--', alpha=0.5)
    elif panel_name == 'obv':
        ax.plot(df.index, df['obv'], label='OBV', color='purple')
    elif panel_name == 'bollinger':
        for col in ['bollinger_upper', 'bollinger_mid', 'bollinger_lower']:
            if col in df.columns:
                ax.plot(df.index, df[col], label=col.replace('bollinger_', '').title(), alpha=0.7)
    elif panel_name == 'supertrend':
        ax.plot(df.index, df['supertrend'], label='Supertrend', color='purple')
    elif panel_name == 'cmf':
        ax.plot(df.index, df['cmf'], label='CMF', color='purple')
        ax.axhline(-0.1, color='green', linestyle='--', alpha=0.5)
        ax.axhline(0.1, color='red', linestyle='--', alpha=0.5)
    elif panel_name == 'vwap':
        ax.plot(df.index, df['vwap'], label='VWAP', color='purple')
    elif panel_name == 'ma':
        for col in df.columns:
            if col.startswith(('sma_', 'ema_')):
                ax.plot(df.index, df[col], label=col, alpha=0.7)
    
    ax.legend()
    ax.grid(True, alpha=0.3)


def show(symbol, timeframe, start_date, end_date):
    st.title("Indicator Experiments")

    all_runners = get_all_indicators()

    with st.sidebar:
        st.subheader("Indicator")
        selected_runner = st.selectbox(
            "Select",
            options=sorted(all_runners),
            format_func=derive_display_name,
            key="indicator_select"
        )

        params = get_indicator_params(selected_runner)
        
        user_params = {}
        for param_name, default_value in params.items():
            if isinstance(default_value, bool):
                user_params[param_name] = st.checkbox(param_name, default_value, key=f"p_{param_name}")
            elif isinstance(default_value, int):
                user_params[param_name] = st.number_input(param_name, value=default_value, step=1, key=f"p_{param_name}")
            elif isinstance(default_value, float):
                user_params[param_name] = st.number_input(param_name, value=float(default_value), step=0.01, key=f"p_{param_name}")
            else:
                user_params[param_name] = st.text_input(param_name, str(default_value), key=f"p_{param_name}")
        params = user_params

        col1, col2 = st.columns(2)
        use_candlestick = col1.checkbox("Candlestick", value=False)
        show_signals = col2.checkbox("Signals", value=True)
        
        run_button = st.button("Run", type="primary")

    if not run_button:
        st.info("Select an indicator and click Run")
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

    st.success(f"Loaded {len(data):,} rows: {data.index[0]} to {data.index[-1]}")

    mod = __import__('robo_trader.indicators', fromlist=[selected_runner])
    run_fn = getattr(mod, selected_runner)
    result_df = run_fn(data.copy(), params)
    
    logger.info(f"Ran {selected_runner} with params: {params}")

    try:
        import matplotlib.pyplot as plt

        sub_panels = discover_sub_panels(result_df)

        n_panels = 1 + len(sub_panels)
        fig, axes = plt.subplots(n_panels, 1, figsize=(14, 3 * n_panels), sharex=True)
        if n_panels == 1:
            axes = [axes]

        price_ax = axes[0]
        if use_candlestick:
            for date, row in result_df.iterrows():
                color = 'green' if row['close'] >= row['open'] else 'red'
                price_ax.plot([date, date], [row['low'], row['high']], color=color, linewidth=1)
                body = abs(row['close'] - row['open'])
                bottom = min(row['open'], row['close'])
                price_ax.fill_between([date - pd.Timedelta(minutes=7), date + pd.Timedelta(minutes=7)],
                                    bottom, bottom + body, color=color, alpha=0.5)
        else:
            price_ax.plot(result_df.index, result_df['close'], label='Close', color='blue', alpha=0.7)

        if show_signals:
            if 'buy_signal' in result_df.columns:
                buy_mask = result_df['buy_signal'] == True
                if buy_mask.any():
                    price_ax.scatter(result_df.index[buy_mask], result_df.loc[buy_mask, 'close'],
                                   color='green', marker='^', s=80, label='Buy', zorder=5)
            if 'sell_signal' in result_df.columns:
                sell_mask = result_df['sell_signal'] == True
                if sell_mask.any():
                    price_ax.scatter(result_df.index[sell_mask], result_df.loc[sell_mask, 'close'],
                                   color='red', marker='v', s=80, label='Sell', zorder=5)

        price_ax.set_title(f'{symbol} {timeframe}')
        price_ax.legend()
        price_ax.grid(True, alpha=0.3)

        for i, (panel_name, config) in enumerate(sub_panels):
            ax = axes[i + 1]
            ax.set_title(config['title'])
            render_sub_panel(ax, panel_name, result_df)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    except Exception as e:
        logger.error(f"Plot error: {e}")
        st.error(f"Plot error: {e}")

    with st.expander("Data"):
        st.dataframe(result_df.tail(50))
