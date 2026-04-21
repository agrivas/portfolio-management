import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging
import json

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
    build_panels,
    get_signal_columns,
    DISPLAY_PANEL_OPTIONS,
)

st.set_page_config(page_title="Indicator Experiments", layout="wide")

st.title("Indicator Experiments")

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

    st.header("Indicators (to Run)")
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

    st.header("Display Panels")
    selected_panels = st.multiselect(
        "Show below price",
        DISPLAY_PANEL_OPTIONS,
        default=['RSI'] if 'RSI' in DISPLAY_PANEL_OPTIONS else None
    )

indicator_params = {}
if selected_indicators:
    params_mode = st.sidebar.radio("Params Mode", ["UI", "JSON"], horizontal=True)
    
    if params_mode == "UI":
        with st.sidebar.expander("Parameters (UI)"):
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
                else:
                    st.caption(f"{ind_name}: no params")
    else:
        st.sidebar.markdown("**Parameters (JSON)**")
        json_input = st.sidebar.text_area(
            "Enter JSON params",
            value="{}",
            height=100,
            help="e.g., {\"rsi_length\": 14, \"rsi_oversold\": 30}"
        )
        try:
            indicator_params = json.loads(json_input)
            st.sidebar.success("Valid JSON")
        except json.JSONDecodeError as e:
            st.sidebar.error(f"Invalid JSON: {e}")
            indicator_params = {}

if not selected_indicators:
    st.warning("Select at least one indicator to run")
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
            with st.empty():
                st.success(f"Loaded {len(data):,} rows: {data.index[0]} to {data.index[-1]}")
                import time
                time.sleep(2)

            result_df = data.copy()
            for ind_name in selected_indicators:
                if params_mode == "JSON":
                    params = {k: v for k, v in indicator_params.items() if not '.' in k}
                else:
                    params = {k.split('.')[1]: v for k, v in indicator_params.items() if k.startswith(f"{ind_name}.")}
                result_df = run_indicator(ind_name, result_df, params)
                logger.info(f"Ran indicator: {ind_name}")

            try:
                panels = build_panels(result_df, selected_panels)
                fig, axes = plot_multi_panel(result_df, panels, figsize=(14, 10))
                st.pyplot(fig)

            except Exception as e:
                logger.error(f"Plot error: {e}")
                st.error(f"Plot error: {e}")
                st.write(result_df.tail(20))

            st.divider()
            
            buy_cols, sell_cols = get_signal_columns(result_df)
            all_signal_cols = buy_cols + sell_cols
            
            if all_signal_cols:
                total_signals = sum(result_df[col].sum() for col in all_signal_cols if col in result_df.columns)
                buy_signals = sum(result_df[col].sum() for col in buy_cols if col in result_df.columns)
                sell_signals = sum(result_df[col].sum() for col in sell_cols if col in result_df.columns)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Signals", total_signals)
                col2.metric("Buy Signals", buy_signals)
                col3.metric("Sell Signals", sell_signals)

            with st.expander("Data"):
                st.dataframe(result_df.tail(50))
    else:
        st.info("👈 Configure and click 'Load & Run'")