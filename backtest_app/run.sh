#!/bin/bash
# Run the Streamlit backtesting app
cd "$(dirname "$0")"

exec poetry run streamlit run app.py "$@"