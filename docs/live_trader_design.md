# Live Trader Design Document

## Overview

This document outlines the architecture and design for a live crypto trading system that runs strategies from the backtester against real Kraken exchange.

**Status**: DRAFT - Pending discussion

---

## 1. Existing Foundation

The codebase already has foundational components:

### Robo-Trader Packages
| Component | File | Purpose |
|-----------|------|---------|
| `CCXTBroker` | `robo-trader/robo_trader/brokers/ccxt_broker.py` | Live order execution via CCXT |
| `CCXTFeed` | `robo-trader/robo_trader/feeds/cctx_feed.py` | OHLCV data from exchanges |
| `Trader.run()` | `robo-trader/robo_trader/trader.py` | Live trading loop (every 60s) |
| `Portfolio` | `robo-trader/robo_trader/portfolio.py` | Position management, persistence |

### Existing Capabilities
- Market/Limit/Stop/TakeProfit/Trailing orders via CCXT
- Real-time price fetching
- Portfolio state autosave every update
- Signal evaluation pattern matching backtester

---

## 2. Execution Model

### Decision: Web + Cron Pings
Web-only architecture. Cron pings the HTTP endpoint every minute.

```
┌─────────────────────────────────────────────────────────┐
│  System Architecture                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ping every 1min    ┌───────────────┐  │
│  │   cron    │ ─────────────────────→ │ HTTP endpoint │  │
│  └──────────┘                       └───────┬───────┘  │
│                                             │           │
│                                             ▼           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  /live_trader/app.py                             │  │
│  │  - Load strategy & config                        │  │
│  │  - Fetch latest candles (if new)                 │  │
│  │  - Evaluate signals                              │  │
│  │  - Execute trades                                │  │
│  │  - Update portfolio state                        │  │
│  │  - Return JSON status                            │  │
│  └──────────────────────────────────────────────────┘  │
│                     │                                  │
│                     ▼                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Kraken via CCXT                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Rationale:**
- Simplicity - each run is isolated, no memory leaks
- Easy to debug/restart
- Streamlit already serves HTTP

---

## 3. Configuration

### Strategy Configuration
Strategies from backtester should be loadable:

```
live_trader/config/
├── strategies.yaml       # Which strategy to run
├── symbols.yaml         # Trading pairs
└── settings.yaml        # Risk parameters
```

### API Key Management

**Option A: Environment Variables (Recommended)**
```bash
export KRAKEN_API_KEY="..."
export KRAKEN_SECRET="..."
```

Clean separation between config and code.

**Option B: Streamlit Secrets**
```toml
# .streamlit/secrets.toml
[kraken]
api_key = "..."
secret = "..."
```

**Option C: Config file**
```yaml
# config.yaml
kraken:
  api_key: "${KRAKEN_API_KEY}"
  secret: "${KRAKEN_SECRET}"
```

### Config Format

**Decision: JSON files**
- Simple, human-readable, easy to edit
- SQLite only if performance becomes unmanageable

```json
{
  "strategy": "adx_ema",
  "symbol": "ETH/GBP",
  "interval": "15m",
  "position_size_pct": 0.25,
  "stop_pct": 0.02,
  "take_profit_pct": 0.06,
  "dry_run": true,
  "enabled": false
}
```

### API Key Management

**Decision: .env file**
- Use `python-dotenv` for loading
- `.env` in root, excluded from git via `.gitignore`
- Standard practice, works with cron

```bash
# .env
KRAKEN_API_KEY=...
KRAKEN_SECRET=...
```

### Symbols

**Decision: Configurable**
- Default: ETH/GBP and XBT/GBP (GBP pairs for UK)
- Loaded from config file
- Single symbol at a time to start

---

## 4. State Persistence

The portfolio already supports JSON persistence:

```
portfolios/
└── portfolio_{uuid}.json
```

Required for live trader:
1. **Load existing portfolio** on startup (resume from crash)
2. **Track trade history** for performance metrics
3. **Trade journal** - all executions with timestamps/errors

### State Files
```
live_trader/
├── state/
│   ├── portfolio.json       # Current positions/cash
│   ├── trade_log.csv       # All executions
│   └── error_log.csv     # Errors for debugging
└── config.yaml            # Configuration
```

---

## 5. Strategy Interface

Strategies must implement:

```python
class Strategy:
    # Required: return interval for data fetching
    interval: str = "15m"
    
    # Required: evaluate and emit signals
    # Returns dict with buy_signal and/or sell_signal
    def evaluate_market(self, symbol, prices, portfolio) -> dict:
        """
        Args:
            symbol: Trading pair (e.g., 'XBT/USD')
            prices: DataFrame with OHLCV + indicators
            portfolio: Current portfolio state
            
        Returns:
            dict with:
                - buy_signal: bool
                - sell_signal: bool
        """
```

---

## 6. Error Handling

Critical for reliable operation:

| Error Type | Handling |
|------------|----------|
| Network failure | Retry 3x with exponential backoff, log error |
| API rate limit | Backoff 60s, continue on next cycle |
| Invalid order | Log error, notify, skip execution |
| Strategy crash | Log full traceback, skip cycle |
| Insufficient balance | Log warning, skip order |

---

## 7. UI Requirements

### Dashboard Pages (Streamlit)

**Page 1: Status Dashboard**
- Current portfolio value & P&L
- Open positions with unrealized P&L
- Last trade executed
- Current prices
- Next evaluation time

**Page 2: Trade History**
- Table of all trades (date, symbol, side, quantity, price, status)
- Filter by date range
- Export to CSV

**Page 3: Configuration**
- Select strategy
- Set position size (% of portfolio)
- Configure stop loss / take profit
- Start/Stop trading

**Page 4: Logs**
- Recent errors
- Trade journal
- System health

### Status Indicators
- 🟢 Running - last cycle successful
- 🟡 Warning - recent errors, continuing
- 🔴 Stopped - requires attention

---

## 8. Implementation Plan

### Phase 1: Foundation
1. Create `live_trader/` directory structure
2. Add API key config loading
3. Implement state file management
4. Create HTTP endpoint (ping handler)

### Phase 2: Integration
1. Connect CCXTBroker for Kraken
2. Make portfolio loadable on startup
3. Create strategy loader (from backtester experiments)
4. Implement error handling & logging

### Phase 3: UI
1. Build Streamlit status page
2. Add trade history view
3. Create configuration page
4. Add logs viewer

### Phase 4: Reliability
1. Add retry logic with backoff
2. Implement health checks
3. Add alerts (optional: Telegram/email)
4. Add position size limits

---

## 9. Decisions Made

1. **Execution Model**: Web + Cron Pings - confirmed
2. **Paper Trading**: Dry-run mode in CCXTBroker - will implement
3. **Config Format**: JSON files (simple files to start)
4. **API Keys**: .env file with python-dotenv
5. **Symbols**: Configurable - ETH/GBP and XBT/GBP to start
6. **State**: Files first, SQLite only if needed

### Risk Parameters (In Config)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `position_size_pct` | 0.25 | % of portfolio per trade |
| `stop_pct` | 0.02 | Stop loss % |
| `take_profit_pct` | 0.06 | Take profit % |
| `max_daily_loss_pct` | 0.10 | Daily loss cap (10%) |

All configurable in config.json

### Paper Trading Mode

**Research Findings:**

Kraken does NOT have a sandbox/testnet for spot trading. However:

1. **CCXT sandbox mode** - `exchange.set_sandbox_mode(True)` works for exchanges that support testnets (Binance, Coinbase). Does NOT work for Kraken spot.

2. **Kraken Futures Demo** - Has a demo environment at `demo-futures.kraken.com` but this is for futures only, not spot trading.

3. **Local Sandbox** - Community project `kraken-sandbox` (GitHub: sudosammy/kraken-sandbox) provides a local mock that simulates Kraken spot API. Useful for testing but doesn't connect to real market prices.

4. **Recommended Approach: Dry-Run Mode**
   - Implement in CCXTBroker: if `dry_run=True`, validate order parameters and log the intended trade but DON'T send to exchange
   - Fetch real prices (so signals are valid) but skip order execution
   - This is the cleanest approach - same code paths, just skip the final API call

```python
# In CCXTBroker:
def create_order(self, ...):
    if self.dry_run:
        logger.info(f"[DRY RUN] Would execute: {order_type} {order_side} {quantity}")
        return Order(id="dry_run_...", status=OrderStatus.FILLED)
    # ... real execution
```

**Decision: Implement dry-run mode in CCXTBroker (Recommended)**

---

## 10. File Structure

```
live_trader/
├── app.py                      # Streamlit app + HTTP handler
├── config.json                 # Configuration
├── .env                       # API keys (gitignored)
├── strategies/               # Strategy loader
│   └── loader.py
├── state/                    # State files
│   ├── portfolio.json        # Current positions/cash
│   ├── trade_log.csv        # All executions
│   └── error_log.csv       # Errors for debugging
├── pages/
│   ├── 1_status.py
│   ├── 2_trades.py
│   ├── 3_config.py
│   └── 4_logs.py
└── requirements.txt
```

---

## 11. My Current Thoughts

### What's Already Ready to Use
1. **CCXTBroker** - Already handles Kraken orders
2. **Portfolio** - Already has save/load, position tracking
3. **Trader.run()** - Has the evaluation loop pattern

### Key Things to Build
1. **Strategy loader** - Load strategies from backtest_app/experiments/strategies/
2. **State management** - Load portfolio on startup, resume from crash
3. **HTTP ping handler** - Endpoint that cron can call
4. **UI pages** - Status, trades, config, logs
5. **Error handling** - Retry logic, comprehensive logging

### Recommended Approach
1. Start with **cron + HTTP** model (simpler, more robust)
2. Use **environment variables** for API keys
3. Add **paper trading mode** first to validate before going live
4. Single strategy, single symbol (XBT/USD) to start

### Priority for Discussion
1. **Execution model** - Confirm cron + HTTP?
2. **Paper trading** - Start with dry-run mode?
3. **Risk limits** - Any position size limits?

---

## 12. Operational Notes

### Streamlit Cache Issues
Streamlit can get stuck in old behaviors. Always clear cache at startup:
```bash
# Clear Streamlit cache
rm -rf .streamlit/__pycache__
rm -rf $VENV/lib/python3.X/site-packages/streamlit/__pycache__
rm -rf $VENV/lib/python3.X/site-packages/streamlit/static
```

### Startup Tips
- Wait ~20 seconds for Streamlit to fully start
- Always test with `curl http://localhost:8502` after startup
- Check `ss -tlnp | grep 8502` to verify port is listening

---

## Appendix: Relevant Code References

| Component | Location |
|-----------|----------|
| CCXTBroker | `robo-trader/robo_trader/brokers/ccxt_broker.py` |
| Portfolio | `robo-trader/robo_trader/portfolio.py` |
| Trader.run() | `robo-trader/robo_trader/trader.py:20-43` |
| Experimental strategies | `backtest_app/experiments/strategies/` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-04-23 | Initial draft |
| 2026-04-23 | Updated decisions (Execution: web+cron, Paper: dry-run, Config: JSON, API: .env) |