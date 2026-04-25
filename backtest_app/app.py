import streamlit as st
import pages.indicators
import pages.strategies

st.set_page_config(
    page_title="Backtesting App",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

st.sidebar.title("Navigation")

page = st.sidebar.radio("Go to", ["Indicator Experiments", "Strategy Backtesting"])

if page == "Indicator Experiments":
    indicators_page.show()
elif page == "Strategy Backtesting":
    strategies_page.show()