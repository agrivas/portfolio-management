#!/bin/bash
cd "$(dirname "$0")"
poetry run uvicorn api:app --host 0.0.0.0 --port 8503