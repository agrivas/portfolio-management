import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_loader import (
    get_available_symbols,
    get_symbol_timeframes,
    get_symbol_stats,
    get_date_range_for_pair,
    load_ohlcv_data,
    AVAILABLE_TIMEFRAMES,
)
from utils.indicators import (
    discover_indicators,
    get_default_params,
    run_indicator,
    plot_multi_panel,
)

st.set_page_config(page_title="Indicator Experiments", layout="wide")

st.title("Indicator Experiments")

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

    timeframes = get_symbol_timeframes(symbol)
    timeframe = st.selectbox(
        "Frequency",
        timeframes,
        index=timeframes.index('15m') if '15m' in timeframes else 0
    )

    info = get_symbol_stats(symbol, timeframe)
    if info:
        st.caption(f"📊 {info.get('rows', 0):,} rows | {info.get('size_mb', 0):.1f} MB")

    st.header("Date Range")
    first_dt, latest_dt = get_date_range_for_pair(symbol, timeframe)
    
    start_date = st.date_input(
        "Start",
        value=(latest_dt - timedelta(days=7)).date(),
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

    st.header("Indicators")
    indicators = discover_indicators()
    if not indicators:
        st.info("No experiments")
        selected_indicators = []
    else:
        selected_indicators = st.multiselect(
            "Select",
            list(indicators.keys()),
            default=list(indicators.keys())[:1] if indicators else None
        )

# Indicator params
indicator_params = {}
if selected_indicators:
    with st.sidebar.expander("Parameters"):
        for ind_name in selected_indicators:
            defaults = get_default_params(ind_name)
            if defaults:
                st.markdown(f"**{ind_name}**")
                cols = st.columns(2)
                for i, (param_name, default_value) in enumerate(defaults.items()):
                    col = cols[i % 2]
                    key = f"{ind_name}_{param_name}"
                    if isinstance(default_value, int):
                        indicator_params[f"{ind_name}.{param_name}"] = col.number_input(
                            param_name, value=int(default_value), key=key
                        )
                    elif isinstance(default_value, float):
                        indicator_params[f"{ind_name}.{param_name}"] = col.number_input(
                            param_name, value=float(default_value), key=key
                        )
                    else:
                        indicator_params[f"{ind_name}.{param_name}"] = col.text_input(
                            param_name, value=str(default_value), key=key
                        )

# RUN BUTTON
if not selected_indicators:
    st.warning("Select at least one indicator")
else:
    run_button = st.sidebar.button("Load & Run", type="primary")

    if run_button:
        logger.info(f"Running indicators: {selected_indicators} for {symbol} {timeframe} {start_date} to {end_date}")
        
        with st.spinner("Loading data..."):
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            
            try:
                data = load_ohlcv_data(symbol, timeframe, start_date=start_dt, end_date=end_dt)
                logger.info(f"Loaded {len(data)} rows")
            except Exception as e:
                logger.error(f"Error loading data: {e}")
                st.error(f"Error: {e}")
                st.stop()

        if data is None or data.empty:
            logger.warning("No data loaded")
            st.error("No data. Try different dates.")
        else:
            # Show transient success message (appears then fades)
            with st.empty():
                st.success(f"Loaded {len(data):,} rows: {data.index[0]} to {data.index[-1]}")
                import time
                time.sleep(2)  # Brief pause so user sees it

            # Run indicators
            result_df = data.copy()
            for ind_name in selected_indicators:
                params = {k.split('.')[1]: v for k, v in indicator_params.items() if k.startswith(f"{ind_name}.")}
                result_df = run_indicator(ind_name, result_df, params)
                logger.info(f"Ran indicator: {ind_name}")

            # Plot first (metrics below)
            try:
                signal_columns = [col for col in result_df.columns if 'signal' in col.lower() or 'buy' in col.lower()]
                
                panels = [
                    {'type': 'price', 'title': f'{symbol}', 
                     'markers': {col: 'green' for col in signal_columns}},
                ]
                
                for col in ['macd', 'macd_signal']:
                    if col in result_df.columns:
                        panels.append({'type': 'line', 'columns': [col], 'title': 'MACD'})
                        break
                
                for col in ['rsi']:
                    if col in result_df.columns:
                        panels.append({'type': 'oscillator', 'column': col, 'title': 'RSI', 'lower': 30, 'upper': 70})
                        break

                fig, axes = plot_multi_panel(result_df, panels, figsize=(14, 10))
                st.pyplot(fig)

            except Exception as e:
                logger.error(f"Plot error: {e}")
                st.error(f"Plot error: {e}")
                st.write(result_df.tail(20))

            # Metrics BELOW the graphs
            st.divider()
            if signal_columns:
                signal_count = sum(result_df[col].sum() for col in signal_columns if col in result_df.columns)
                logger.info(f"Total signals: {signal_count}")
                st.metric("Total Signals", signal_count)

            with st.expander("Data"):
                st.dataframe(result_df.tail(50))
    else:
        st.info("👈 Configure and click 'Load & Run'")