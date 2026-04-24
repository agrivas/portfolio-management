# Portfolio Management

Personal crypto portfolio management, automated trading strategy backtesting, and technical indicator research.

## Packages & Folders

| Folder | Purpose |
|--------|---------|
| `/` | Root - poetry project, notebooks |
| `advanced-ta/` | Technical analysis library (Lorentzian Classification) |
| `robo-trader/` | Trading library package |
| `backtest_app/` | Streamlit app for strategy development |
| `live_trader/` | Live trading Streamlit app |
| `notebooks/` | Jupyter notebooks (legacy) |
| `data/` | **IGNORED** - data files |

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
# Install dependencies
poetry install

# Run backtest app
cd backtest_app && poetry run streamlit run app.py

# Run tests
cd robo-trader && poetry run pytest
```

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

## Notes

- **Data excluded**: Large files + potentially private (in .gitignore)
- **Tests location**: robo-trader tests must run from robo-trader/ directory
- **Python version**: 3.10