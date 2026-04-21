# Indicator Experiments

This folder contains indicator experiments for the backtesting app.

## File Structure

Each indicator is a single `.py` file with:
- `PARAMS`: dict of configurable parameters with defaults
- `run(df, params) -> df`: function that computes indicators and returns the modified DataFrame

## Required Output Columns

### Signal Columns (for plotting markers on main graph)

| Column | Type | Description |
|--------|------|-------------|
| `buy_signal` | bool | Buy condition met (green ▲ marker) |
| `sell_signal` | bool | Sell condition met (red ▼ marker) |

**Important**: Always set BOTH columns. If your indicator only generates buy signals, set `sell_signal = False` (and vice versa).

## Example: Running an Indicator

```python
import pandas as pd
import pandas_ta as pta

PARAMS = {
    'fast': 12,
    'slow': 26,
    'signal': 9,
}

def run(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    fast = params.get('fast', PARAMS['fast'])
    slow = params.get('slow', PARAMS['slow'])
    signal = params.get('signal', PARAMS['signal'])
    
    macd = pta.macd(df['close'], fast=fast, slow=slow, signal=signal)
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 2]
        df['macd_hist'] = macd.iloc[:, 1]
        
        df['macd_cross_up'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df['macd_cross_down'] = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        df['buy_signal'] = df['macd_cross_up'].fillna(False)
        df['sell_signal'] = df['macd_cross_down'].fillna(False)
    
    return df
```

## Adding a New Indicator

1. Create a new `.py` file in this folder (e.g., `my_indicator.py`)
2. Define `PARAMS` with your default values
3. Implement `run(df, params) -> df` function
4. Set `buy_signal` and `sell_signal` columns

## Parameter Customization

Parameters can be customized in the UI:
- **UI Mode**: Use the number input fields in the sidebar
- **JSON Mode**: Enter parameters as JSON, e.g., `{"length": 14, "oversold": 30}`

## Display Panels

Select which primitive indicators to display below the price chart. These are independent of which indicators you run.

| Panel | Required Columns | Description |
|-------|------------------|-------------|
| MACD | `macd`, `macd_signal`, `macd_hist` | Moving Average Convergence Divergence |
| RSI | `rsi` | Relative Strength Index (30/70 thresholds) |
| CCI | `cci` | Commodity Channel Index (-250/+250 thresholds) |
| ADX | `adx` | Average Directional Index (25 threshold) |
| MFI | `mfi` | Money Flow Index (20/80 thresholds) |
| Bollinger | `bollinger_mid`, `bollinger_upper`, `bollinger_lower` | Bollinger Bands |
| Supertrend | `supertrend` | Supertrend indicator |
| ATR | `atr` | Average True Range (volatility) |
| Moving Averages | `ema_*`, `sma_*` | EMAs and SMAs (first 5) |

## Available Indicators

| Indicator | Description | Creates Columns |
|-----------|-------------|-----------------|
| `macd` | MACD crossover | `macd`, `macd_signal`, `buy_signal`, `sell_signal` |
| `rsi` | RSI oversold/overbought | `rsi`, `buy_signal`, `sell_signal` |
| `cci` | CCI extremes | `cci`, `buy_signal`, `sell_signal` |
| `bollinger` | Bollinger Bands breakout | `bollinger_*`, `buy_signal`, `sell_signal` |
| `supertrend` | Supertrend direction | `supertrend`, `buy_signal`, `sell_signal` |
| `adx` | ADX trend strength | `adx`, `buy_signal`, `sell_signal` |
| `mfi` | MFI extremes | `mfi`, `buy_signal`, `sell_signal` |
| `adx_sma_cci` | Combined ADX + SMA + CCI | `cci`, `sma_*`, `adx`, `buy_signal` |
| `adx_ema_rsi` | ADX + EMA + RSI + V-shape | Multiple, `buy_signal`, `sell_signal` |
| `adx_ema` | ADX + EMA crossover | `adx`, `ema_*`, `buy_signal`, `sell_signal` |
| `rsi_sma_adx` | RSI + SMA + ADX | `rsi_*`, `sma_*`, `adx`, `buy_signal` |
| `rsi_v_recovery` | RSI V-recovery pattern | `rsi`, `v_recovery`, `buy_signal` |

**Note**: Composite indicators generate signals but don't auto-display panels. Use the "Display Panels" section to add RSI, MACD, etc. below the chart.