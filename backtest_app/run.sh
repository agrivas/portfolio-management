#!/bin/bash
# Run the Streamlit backtesting app
cd "$(dirname "$0")"

exec streamlit run backtest_app/app.py "$@"