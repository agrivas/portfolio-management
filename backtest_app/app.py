import streamlit as st
from datetime import datetime, timedelta

from utils.data_loader import get_available_symbols, get_symbol_timeframes, get_symbol_stats, get_date_range_for_pair

st.set_page_config(page_title="Backtesting App", layout="wide")

st.sidebar.title("Backtesting App")

page = st.sidebar.radio("Go to", ["Indicator Experiments", "Strategy Backtesting"])

available_symbols = get_available_symbols()
if not available_symbols:
    st.error("No data available")
    st.stop()

symbol = st.sidebar.selectbox("Symbol", available_symbols)

timeframes = get_symbol_timeframes(symbol)
timeframe = st.sidebar.selectbox("Frequency", timeframes, index=timeframes.index('15m') if '15m' in timeframes else 0)

info = get_symbol_stats(symbol, timeframe)
if info:
    st.sidebar.caption(f"📊 {info.get('rows', 0):,} rows | {info.get('size_mb', 0):.1f} MB")

first_dt, latest_dt = get_date_range_for_pair(symbol, timeframe)
start_date = st.sidebar.date_input("Start", value=(latest_dt - timedelta(days=7)).date(), min_value=first_dt.date(), max_value=latest_dt.date())
end_date = st.sidebar.date_input("End", value=latest_dt.date(), min_value=first_dt.date(), max_value=latest_dt.date())
st.sidebar.caption(f"📅 {(end_date - start_date).days} days")

if page == "Indicator Experiments":
    from views import indicators as indicators_page
    indicators_page.show(symbol, timeframe, start_date, end_date)
elif page == "Strategy Backtesting":
    from views import strategies as strategies_page
    strategies_page.show(symbol, timeframe, start_date, end_date)