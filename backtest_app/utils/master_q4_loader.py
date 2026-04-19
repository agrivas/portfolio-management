"""Master Q4 OHLCV data loader - no resampling, direct CSV read."""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import pandas as pd
from pathlib import Path

MASTER_Q4_DIR = Path('/workspaces/portfolio-management/data/kraken/master_q4')
REGISTRY_FILE = Path('/workspaces/portfolio-management/data/kraken/master_q4_registry.json')

TIMEFRAME_MAP = {
    '1': '1m',
    '5': '5m', 
    '15': '15m',
    '30': '30m',
    '60': '1h',
    '240': '4h',
    '720': '12h',
    '1440': '1d',
}

TIMEFRAME_MINUTES = {v: int(k) for k, v in TIMEFRAME_MAP.items()}

AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '1d']


def load_registry() -> Dict:
    """Load or build registry."""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, 'r') as f:
            return json.load(f)
    return {}


def build_registry():
    """Build registry from master_q4 files (first/last timestamps, row estimate)."""
    registry = {}
    
    for f in MASTER_Q4_DIR.glob('*.csv'):
        # Parse: SYMBOL_TIMEFRAME.csv (e.g., XBTUSD_15.csv)
        name = f.stem
        if '_' not in name:
            continue
            
        parts = name.rsplit('_', 1)
        if len(parts) != 2:
            continue
            
        symbol, tf = parts
        if tf not in TIMEFRAME_MAP:
            continue
            
        tf_name = TIMEFRAME_MAP[tf]
        
        try:
            file_size = os.path.getsize(f)
            rows = file_size // 50  # ~50 bytes per line estimate
            
            # Read first timestamp
            with open(f, 'r') as fh:
                first_line = fh.readline()
            first_ts = int(first_line.split(',')[0])
            
            # Read last timestamp (seek to end)
            with open(f, 'rb') as fh:
                fh.seek(-200, 2)
                last_lines = fh.readlines()
            last_line = last_lines[-1]
            last_ts = int(last_line.split(b',')[0])
            
            first_dt = datetime.utcfromtimestamp(first_ts)
            last_dt = datetime.utcfromtimestamp(last_ts)
            
            if symbol not in registry:
                registry[symbol] = {}
            
            registry[symbol][tf_name] = {
                'first': first_dt.strftime('%Y-%m-%d'),
                'latest': last_dt.strftime('%Y-%m-%d'),
                'rows': rows,
                'size_mb': round(file_size / (1024*1024), 1),
            }
            
        except Exception as e:
            print(f"Error processing {f}: {e}")
            continue
    
    # Save registry
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(registry, f, indent=2)
    
    return registry


def get_registry() -> Dict:
    """Get registry, building if needed."""
    reg = load_registry()
    if not reg:
        print("Building registry...")
        reg = build_registry()
    return reg


def get_symbols() -> List[str]:
    """Get all available symbols."""
    reg = get_registry()
    return sorted(reg.keys(), key=lambda x: reg.get(x, {}).get('15m', {}).get('rows', 0), reverse=True)


def get_available_timeframes(symbol: str) -> List[str]:
    """Get available timeframes for a symbol."""
    reg = get_registry()
    symbol_data = reg.get(symbol, {})
    return sorted(symbol_data.keys(), key=lambda x: TIMEFRAME_MINUTES.get(x, 0))


def get_symbol_info(symbol: str, timeframe: str) -> Dict:
    """Get metadata for symbol + timeframe."""
    reg = get_registry()
    return reg.get(symbol, {}).get(timeframe, {})


def get_date_range(symbol: str, timeframe: str) -> tuple:
    """Get (first_date, latest_date) for symbol/timeframe."""
    info = get_symbol_info(symbol, timeframe)
    if not info:
        return datetime(2020, 1, 1), datetime.now()
    first = datetime.strptime(info['first'], '%Y-%m-%d')
    latest = datetime.strptime(info['latest'], '%Y-%m-%d')
    return first, latest


def load_data(
    symbol: str,
    timeframe: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days: Optional[int] = None,
) -> pd.DataFrame:
    """Load OHLCV data for symbol + timeframe.
    
    Args:
        symbol: e.g., 'XBTUSD'
        timeframe: e.g., '15m'
        start_date: Start datetime (optional)
        end_date: End datetime (optional)  
        days: If set and no dates, load last N days
    
    Returns:
        DataFrame with columns: [open, high, low, close, volume, trades]
    """
    # Build filepath
    tf_id = TIMEFRAME_MINUTES.get(timeframe, '15')
    filepath = MASTER_Q4_DIR / f"{symbol}_{tf_id}.csv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # Read CSV - no filtering yet
    df = pd.read_csv(
        filepath,
        names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades'],
        dtype={
            'timestamp': 'int64',
            'open': 'float64',
            'high': 'float64', 
            'low': 'float64',
            'close': 'float64',
            'volume': 'float64',
            'trades': 'int64',
        }
    )
    
    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df = df.set_index('timestamp')
    df = df.sort_index()
    
    # Filter by date if provided
    if start_date is not None:
        if isinstance(start_date, datetime):
            start_date = pd.Timestamp(start_date, tz='UTC')
        if start_date.tzinfo is None:
            start_date = start_date.tz_localize('UTC')
        df = df[df.index >= start_date]
    
    if end_date is not None:
        if isinstance(end_date, datetime):
            end_date = pd.Timestamp(end_date, tz='UTC')
        if end_date.tzinfo is None:
            end_date = end_date.tz_localize('UTC')
        df = df[df.index <= end_date]
    
    # Apply days limit if no specific dates
    if days is not None and start_date is None and end_date is None:
        cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        df = df[df.index >= cutoff]
    
    return df


def get_data_info(df: pd.DataFrame) -> dict:
    """Get data summary."""
    return {
        'rows': len(df),
        'start': df.index[0] if len(df) > 0 else None,
        'end': df.index[-1] if len(df) > 0 else None,
    }