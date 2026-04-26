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

**CRITICAL RULES:**
- **NEVER destroy the venv** (.venv) unless directly asked to do so
- **robo-trader** and **advanced-ta** are included in the main project with `develop = true` - their changes are reflected automatically without reinstalling
- Use **AT LEAST 10 minutes timeout** for any terminal command; if you think it will take longer (e.g., poetry install), prompt the user first

```bash
# Install dependencies (allow 5-10 minutes)
poetry install

# Run backtest app
cd backtest_app && poetry run streamlit run app.py

# Run tests
cd robo-trader && poetry run pytest
```

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

1. Changes to packages with `develop = true` are **automatically reflected** in the venv - no manual sync needed
2. Test via `poetry run` commands, not direct python execution
3. If changes don't appear, ask user before attempting full reinstall

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

### Adding New Strategies

New strategies are defined in `robo-trader/robo_trader/strategies/` and automatically discovered by the backtest app.

```python
# robo-trader/robo_trader/strategies/my_strategy.py
from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
import pandas as pd

PARAMS = {
    'position_size': 1.0,
    'rsi_length': 14,
    'rsi_oversold': 30,
}

class MyStrategy(Strategy):
    def __init__(self, params: dict):
        super().__init__()
        self.position_size = params.get('position_size', PARAMS['position_size'])
        ...

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        # Trading logic
        ...
```

Then add to `robo-trader/robo_trader/strategies/__init__.py`:
```python
from .my_strategy import MyStrategy, PARAMS as my_strategy_params
# Add to STRATEGY_PARAMS dict
# Add to __all__ via list(STRATEGY_PARAMS.keys())
```

### Adding New Indicators

New indicators are defined in `robo-trader/robo_trader/indicators/` and automatically discovered by the backtest app.

```python
# robo-trader/robo_trader/indicators/my_indicator.py
import pandas as pd

PARAMS = {
    'length': 14,
    'threshold': 30,
}

def run(df, params):
    df['my_indicator'] = ...
    return df
```

Then add to `robo-trader/robo_trader/indicators/__init__.py`:
```python
from .my_indicator import run as run_my_indicator, PARAMS as my_indicator_params
# Add to INDICATOR_PARAMS dict
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