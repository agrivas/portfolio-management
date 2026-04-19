import streamlit as st

st.set_page_config(
    page_title="Backtesting App",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", ["Indicator Experiments", "Strategy Backtesting"])

if page == "Indicator Experiments":
    import pages.indicators as indicators_page
elif page == "Strategy Backtesting":
    import pages.strategies as strategies_page