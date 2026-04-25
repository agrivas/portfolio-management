#!/bin/bash
cd "$(dirname "$0")"
poetry run streamlit cache clear
poetry run streamlit run app.py -- --server.port 8502