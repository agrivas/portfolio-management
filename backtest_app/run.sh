#!/bin/bash
# Run the Streamlit backtesting app
cd "$(dirname "$0")"

poetry run streamlit cache clear
poetry run streamlit run app.py "$@"