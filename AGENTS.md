# Portfolio Management

Personal crypto portfolio management, automated trading strategy backtesting, and technical indicator research.

## Packages & Folders

| Folder | Purpose |
|--------|---------|
| `/` | Root - poetry project, notebooks |
| `advanced-ta/` | Technical analysis library (Lorentzian Classification) |
| `robo-trader/` | Trading library package |
| `backtest_app/` | Streamlit app for strategy development |
| `live_trader/` | Live trading API (FastAPI) + Streamlit UI |
| `notebooks/` | Jupyter notebooks (legacy) |
| `data/` | **IGNORED** - data files |

## robo_trader Architecture

The purpose of `robo_trader` is to abstract the process of trading and backtest by defining key components:

| Component | Purpose |
|------------|---------|
| **Broker** | Abstraction for exchange connectivity (create_order, get_balance, sync) |
| **Portfolio** | Manages cash, holdings, positions, state persistence |
| **Feed** | Abstraction for market data (historical or live) |
| **Strategy** | Evaluates market conditions and generates signals |

Standardized interaction between components ensures strategies work identically in backtest and live trading.

## Symbols

Available trading pairs (for live trading via CCXT/Kraken):
- ETH/BTC (Ethereum / Bitcoin)
- ETH/GBP (Ethereum / Pound)
- BTC/GBP (Bitcoin / Pound)
- SOL/BTC (Solana / Bitcoin)
- SOL/GBP (Solana / Pound)

**Note**: Historical data in `data/kraken/` may use different symbols - live trading uses CCXT unified symbols which map Kraken's internal format (XBT → BTC).

## Development

```bash
# Install dependencies (allow up to 5 minutes)
poetry install

# Run backtest app
cd backtest_app && poetry run streamlit run app.py

# Run tests
cd robo-trader && poetry run pytest
```

**Note:** poetry install can take several minutes. Use a longer timeout if needed.

### Import Guidelines

ALL imports should be at the TOP of the file, after any `if __name__ == "__main__":` guard (if present).

| Do | Don't |
|-----|-------|
| Import at top | Import inside functions |
| Use absolute imports | Lazy loading |
| Use proper path deps | sys.path manipulation |

**Exception:** Only use late imports when avoiding circular import issues.

### Package Updates Workflow

When modifying code in `robo-trader/` package (e.g., adding methods to brokers):

1. **ALWAYS** run `poetry install` to sync changes to `.venv`
2. **NEVER** manually copy files between `.venv` and source
3. Test via `poetry run` commands, not direct python execution
4. If changes don't appear, try: `rm -rf .venv && poetry install` (full reinstall)

**Note**: Path dependencies sometimes cache stale. If code changes don't appear after install, force a full reinstall:
```bash
rm -rf .venv
poetry install
```

Example:
```bash
# After editing robo-trader/robo_trader/brokers/ccxt_broker.py:
poetry install  # Refreshes .venv with updated code

# If that doesn't work:
rm -rf .venv && poetry install
```

## backtest_app

Streamlit application for indicator experimentation and strategy backtesting.

### Running
```bash
cd backtest_app
streamlit run app.py
# Or: ./run.sh
```

### Pages
- **Indicator Experiments** - Test indicator combinations visually
- **Strategy Backtesting** - Run strategy backtests with P&L

### Adding New Experiments

**Indicators** (`backtest_app/experiments/indicators/`):
```python
PARAMS = {'param1': 14, 'param2': 30}

def run(df, params):
    # Compute indicators
    df['rsi'] = ...
    df['signal'] = (condition)
    return df
```

**Strategies** (`backtest_app/experiments/strategies/`):
```python
class MyStrategy(Strategy):
    def evaluate_market(self, symbol, prices, portfolio):
        # Trading logic
        portfolio.open_long(...)
```

## Data Sources (IGNORED)

Data is stored in `/data/` but excluded from git.

### Kraken OHLCV Data (`data/kraken/`)
- XBT, ETH, XRP, BNB, SOL paired with USD, EUR, GBP
- Pre-aggregated to timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d
- Date range: 2013 to late 2025

### Portfolio Data (`data/portfolio/`)
- CSV files from Trading 212

## Key APIs

### KrakenCSVFeed
```python
from robo_trader.feeds import KrakenCSVFeed

feed = KrakenCSVFeed(interval="15m")
data = feed.get_data("XBTUSD")
```

## Package Dependencies

- **Root** (`pyproject.toml`): Depends on advanced-ta, robo-trader, streamlit, pandas, pandas_ta
- **robo-trader**: Depends on advanced-ta, yfinance, ta
- **advanced-ta**: No dependencies

## Live Trader

Automated trading via Kraken API with FastAPI backend + Streamlit UI.

### Architecture

```
Port 8503 (API):  FastAPI - holds all logic, talks to Kraken
Port 8501 (UI):    Streamlit - dumb frontend, calls API
Cron:              Hits /trading-cycle every minute
```

### Running

```bash
# Terminal 1: API (port 8503)
cd live_trader
poetry run uvicorn api:app --host 0.0.0.0 --port 8503

# Terminal 2: UI (port 8501)
cd live_trader
poetry run streamlit run app.py
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/trading-cycle` | Run cycle (cron hits this) |
| GET | `/status` | Current price, balance, config |
| GET | `/logs` | Event logs with filtering |
| GET | `/trades` | Trade history |
| GET | `/config` | Get current config |
| POST | `/config` | Update config |

### Cron Setup

```bash
# Every minute
* * * * * curl -X POST http://localhost:8503/trading-cycle
```

### Notes

- **Data excluded**: Large files + potentially private (in .gitignore)
- **Tests location**: robo-trader tests must run from robo-trader/ directory
- **Python version**: 3.10