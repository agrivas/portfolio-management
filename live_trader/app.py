import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Live Trader", page_icon="📈", layout="wide")

from config import load_config, save_config, get_kraken_credentials
from state import get_trade_log, get_error_log, get_event_log, load_portfolio_state
from strategies.loader import list_strategies
from trader import run_trading_cycle

st.title("📈 Live Trader")

config = load_config()

if "last_update" not in st.session_state:
    st.session_state.last_update = None

tab1, tab2, tab3, tab4 = st.tabs(["Status", "Trades", "Config", "Logs"])

with tab1:
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    status = "✅ Enabled" if config.get("enabled", False) else "⏸️ Disabled"
    
    try:
        from robo_trader.brokers import CCXTBroker
        api_key, secret = get_kraken_credentials()
        if api_key and secret:
            broker = CCXTBroker("kraken", api_key, secret)
            current_price = broker.get_price(config.get("symbol", "ETH/BTC"))
            balance = broker.get_balance()
    except Exception as e:
        current_price = 0
        balance = None
    
    with col1:
        st.metric("Pair", config.get("symbol", "ETH/GBP"))
    with col2:
        if current_price > 0:
            st.metric("Price", f"{current_price:,.2f}")
        else:
            st.metric("Price", "N/A")
    with col3:
        st.metric("Status", status)
    
    st.divider()
    
    # Portfolio Balance Table
    st.subheader("Portfolio Balance")
    if balance:
        balance_data = []
        for currency, free_amt in balance.get('free', {}).items():
            if free_amt and free_amt > 0:
                total_amt = balance.get('total', {}).get(currency, free_amt)
                used_amt = balance.get('used', {}).get(currency, 0)
                balance_data.append({
                    "Currency": currency,
                    "Available": f"{free_amt:.6f}",
                    "Used": f"{used_amt:.6f}",
                    "Total": f"{total_amt:.6f}"
                })
        
        if balance_data:
            st.dataframe(
                pd.DataFrame(balance_data),
                hide_index=True,
                width='stretch'
            )
        else:
            st.info("No funds available")
    else:
        st.info("Unable to fetch balance")
    
    st.divider()
    
    if st.button("🚀 Run Trading Cycle", type="primary"):
        with st.spinner("Running..."):
            result = run_trading_cycle()
            st.session_state.last_update = result
            if result.get("status") == "success":
                st.success(f"Cycle complete: {len(result.get('trades', []))} trades executed")
            else:
                st.error(f"Error: {result.get('message', 'Unknown error')}")
    
    if st.session_state.last_update:
        st.subheader("Last Result")
        st.json(st.session_state.last_update)

with tab2:
    st.subheader("Trade History")
    
    trades = get_trade_log(100)
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
    
    with st.form("config_form"):
        strategy = st.selectbox(
            "Strategy",
            options=list_strategies(),
            index=list_strategies().index(config.get("strategy", "adx_ema")) if config.get("strategy") in list_strategies() else 0
        )
        
        symbol = st.selectbox(
            "Symbol",
            options=["ETH/BTC", "ETH/GBP", "BTC/GBP", "SOL/BTC", "SOL/GBP"],
            index=0
        )
        interval = st.selectbox("Interval", options=["1m", "5m", "15m", "1h", "4h", "1d"], index=2)
        
        col1, col2 = st.columns(2)
        with col1:
            position_size = st.slider("Position Size %", 0.01, 1.0, config.get("position_size_pct", 0.25), 0.01)
        with col2:
            stop_pct = st.slider("Stop Loss %", 0.01, 0.10, config.get("stop_pct", 0.02), 0.01)
        
        col3, col4 = st.columns(2)
        with col3:
            take_profit_pct = st.slider("Take Profit %", 0.02, 0.20, config.get("take_profit_pct", 0.06), 0.01)
        with col4:
            enabled = st.toggle("Enable Trading", value=config.get("enabled", False))
        
        submitted = st.form_submit_button("Save Configuration")
        if submitted:
            config["strategy"] = strategy
            config["symbol"] = symbol
            config["symbol_internal"] = symbol.replace("/", "")[:6]
            config["interval"] = interval
            config["position_size_pct"] = position_size
            config["stop_pct"] = stop_pct
            config["take_profit_pct"] = take_profit_pct
            config["enabled"] = enabled
            save_config(config)
            st.success("Configuration saved!")
            st.rerun()

with tab4:
    st.subheader("Logs")
    
    severity_filter = st.multiselect(
        "Filter by severity",
        options=["INFO", "WARNING", "ERROR"],
        default=["INFO", "WARNING", "ERROR"]
    )
    
    events = get_event_log(200)
    if events:
        df = pd.DataFrame(events)
        if severity_filter:
            df = df[df['severity'].isin(severity_filter)]
        st.dataframe(
            df,
            width='stretch',
            hide_index=True
        )
    else:
        st.info("No events logged")
    
    st.divider()
    
    st.subheader("System Info")
    portfolio = load_portfolio_state()
    if portfolio:
        st.json(portfolio)
    else:
        st.info("No portfolio state")