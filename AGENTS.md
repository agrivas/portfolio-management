# Portfolio Management

Personal crypto portfolio management, automated trading strategy backtesting, and technical indicator research.

## Packages & Folders

| Folder | Purpose |
|--------|---------|
| `/` | Root - poetry project, notebooks |
| `advanced-ta/` | Technical analysis library (Lorentzian Classification) |
| `robo-trader/` | Trading library package |
| `backtest_app/` | Streamlit app for strategy development |
| `notebooks/` | Jupyter notebooks (legacy) |
| `data/` | **IGNORED** - data files |

## Development

```bash
# Install dependencies
poetry install

# Run backtest app
cd backtest_app && poetry run streamlit run app.py

# Run tests
cd robo-trader && poetry run pytest
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

### Kraken OHLCV Data (`data/kraken/master_q4/`)
- XBTUSD, ETHUSD, SOLUSD (with EUR/GBP/USDT variants)
- Pre-aggregated to timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d
- Date range: 2013 to late 2025

### Portfolio Data (`data/portfolio/`)
- CSV files from Trading 212

## Key APIs

### KrakenCSVFeed
```python
from robo_trader.feeds import KrakenCSVFeed

feed = KrakenCSVFeed(
    data_dir="/data/kraken/master_q4",
    interval="15m"
)
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