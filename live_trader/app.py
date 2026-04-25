import streamlit as st
import pandas as pd
import requests
from datetime import datetime

API_BASE = "http://localhost:8503"

st.set_page_config(page_title="Live Trader", page_icon="📈", layout="wide")

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True


def call_api(endpoint: str, method: str = "GET", data: dict = None):
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            return requests.get(url, timeout=30).json()
        else:
            return requests.post(url, json=data, timeout=60).json()
    except Exception as e:
        return {"error": str(e)}


st.title("📈 Live Trader")

tab1, tab2, tab3, tab4 = st.tabs(["Status", "Trades", "Config", "Logs"])

with tab1:
    st.subheader("System Status")
    
    status = call_api("/status")
    
    col1, col2, col3 = st.columns(3)
    
    settings = status.get("settings", {})
    state = status.get("state", {})
    
    with col1:
        st.metric("Pair", settings.get("symbol", "N/A"))
    with col2:
        st.metric("Cash", f"£{state.get('cash', 0):.2f}" if state else "N/A")
    with col3:
        st.metric("Holdings", str(state.get("asset_holdings", {})) if state else "N/A")
    
    st.divider()
    
    st.divider()
    
    if st.button("🚀 Run Trading Cycle", type="primary"):
        with st.spinner("Running..."):
            result = call_api("/trading-cycle", "POST")
            if result.get("status") == "success":
                st.success(f"Cycle complete: {len(result.get('trades', []))} trades executed")
            else:
                st.error(f"Error: {result.get('message', 'Unknown error')}")
        st.rerun()
    
    st.divider()
    
    st.subheader("Last Result")
    st.json(status)

with tab2:
    st.subheader("Trade History")
    
    trades = call_api("/trades")
    if trades:
        st.dataframe(
            pd.DataFrame(trades),
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No trades yet")

with tab3:
    st.subheader("Configuration")
    
    config = call_api("/config") or {}
    strategies = call_api("/strategies")
    
    if not config:
        st.warning("No portfolio configured. Set your preferences below to create one.")
    
    with st.form("config_form"):
        strategy = st.selectbox(
            "Strategy",
            options=strategies,
            index=strategies.index(config.get("strategy", "adx_ema")) if config.get("strategy") in strategies else 0
        )
        
        symbol = st.selectbox(
            "Symbol",
            options=["ETH/BTC", "ETH/GBP", "BTC/GBP", "SOL/BTC", "SOL/GBP"],
            index=["ETH/BTC", "ETH/GBP", "BTC/GBP", "SOL/BTC", "SOL/GBP"].index(config.get("symbol", "ETH/GBP")) if config.get("symbol") in ["ETH/BTC", "ETH/GBP", "BTC/GBP", "SOL/BTC", "SOL/GBP"] else 1
        )
        interval = st.selectbox("Interval", options=["1m", "5m", "15m", "1h", "4h", "1d"], index=["1m", "5m", "15m", "1h", "4h", "1d"].index(config.get("interval", "15m")) if config.get("interval") in ["1m", "5m", "15m", "1h", "4h", "1d"] else 2)
        
        col1, col2 = st.columns(2)
        with col1:
            position_size = st.slider("Position Size %", 0.01, 1.0, config.get("position_size_pct", 0.5), 0.01)
        with col2:
            stop_pct = st.slider("Stop Loss %", 0.01, 0.10, config.get("stop_pct", 0.01), 0.01)
        
        col3, col4 = st.columns(2)
        with col3:
            take_profit_pct = st.slider("Take Profit %", 0.02, 0.20, config.get("take_profit_pct", 0.1), 0.01)
        
        submitted = st.form_submit_button("Save Configuration")
        if submitted:
            result = call_api("/config", "POST", {
                "strategy": strategy,
                "symbol": symbol,
                "interval": interval,
                "position_size_pct": position_size,
                "stop_pct": stop_pct,
                "take_profit_pct": take_profit_pct
            })
            if result.get("success"):
                st.success("Configuration saved!")
                st.rerun()
            else:
                st.error(f"Error saving config: {result}")

with tab4:
    st.subheader("Logs")
    
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.multiselect(
            "Filter by severity",
            options=["INFO", "WARNING", "ERROR"],
            default=["INFO", "WARNING", "ERROR"]
        )
    with col2:
        limit = st.slider("Max logs", 10, 500, 100)
    
    severity_param = ",".join(severity_filter) if severity_filter else None
    logs = call_api(f"/logs?severity={severity_param}&limit={limit}")
    
    if logs:
        df = pd.DataFrame(logs)
        st.dataframe(
            df,
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No events logged")
    
    st.divider()


auto_refresh = st.checkbox("Auto-refresh (every 60s)", value=st.session_state.auto_refresh)
if auto_refresh != st.session_state.auto_refresh:
    st.session_state.auto_refresh = auto_refresh

if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()