#!/bin/bash
# Run the Streamlit backtesting app
cd "$(dirname "$0")"

exec streamlit run streamlit_app/app.py "$@"