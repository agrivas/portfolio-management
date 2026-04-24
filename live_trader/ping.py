#!/usr/bin/env python3
"""
HTTP ping endpoint for live trader.
Run with: uvicorn ping:app --host 0.0.0.0 --port 8000
Or call directly: python3 ping.py
"""
import sys
from pathlib import Path
from fastapi import FastAPI
import uvicorn

sys.path.insert(0, str(Path(__file__).parent))

from trader import run_trading_cycle

app = FastAPI()

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

@app.get("/trade")
def trade():
    result = run_trading_cycle()
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)