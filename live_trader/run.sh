#!/bin/bash
cd /workspaces/portfolio-management/live_trader
poetry run streamlit run app.py --server.headless=true --server.port=8502