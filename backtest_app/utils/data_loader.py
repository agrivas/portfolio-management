"""Data loader - uses master_q4 OHLCV data (no resampling)."""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import pandas as pd

from .master_q4_loader import (
    get_registry,
    get_symbols,
    get_available_timeframes,
    get_symbol_info,
    get_date_range as _get_date_range,
    load_data as _load_data_from_master,
    AVAILABLE_TIMEFRAMES,
)

# Re-export for convenience
__all__ = [
    'get_available_symbols',
    'get_symbol_timeframes',
    'get_symbol_stats',
    'get_date_range_for_pair',
    'load_ohlcv_data',
    'AVAILABLE_TIMEFRAMES',
]


def get_available_symbols() -> List[str]:
    return get_symbols()


def get_symbol_timeframes(symbol: str) -> List[str]:
    return get_available_timeframes(symbol)


def get_symbol_stats(symbol: str, timeframe: str) -> Dict[str, Any]:
    return get_symbol_info(symbol, timeframe)


def get_date_range_for_pair(symbol: str, timeframe: str) -> tuple:
    return _get_date_range(symbol, timeframe)


def load_ohlcv_data(
    symbol: str,
    timeframe: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days: Optional[int] = None,
) -> pd.DataFrame:
    return _load_data_from_master(symbol, timeframe, start_date, end_date, days)


def get_data_info(df: pd.DataFrame) -> dict:
    return {
        'rows': len(df),
        'start': df.index[0] if len(df) > 0 else None,
        'end': df.index[-1] if len(df) > 0 else None,
        'columns': list(df.columns),
    }