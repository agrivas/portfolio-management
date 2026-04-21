"""Data loader - uses KrakenCSVFeed with hardcoded pairs."""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'robo-trader'))

from robo_trader.feeds import KrakenCSVFeed


KRACKEN_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'kraken')

AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '4h', '12h', '1d']

AVAILABLE_PAIRS = {
    'XBTUSD', 'XBTEUR', 'XBTGBP',
    'ETHUSD', 'ETHEUR', 'ETHGBP',
    'XRPUSD', 'XRPEUR', 'XRPGBP',
    'BNBUSD', 'BNBEUR',
    'SOLUSD', 'SOLEUR', 'SOLGBP',
}


def get_available_symbols() -> List[str]:
    return sorted(AVAILABLE_PAIRS)


def get_symbol_timeframes(symbol: str) -> List[str]:
    return AVAILABLE_TIMEFRAMES


def get_symbol_stats(symbol: str, timeframe: str) -> Dict:
    return {}


def get_date_range_for_pair(symbol: str, timeframe: str) -> tuple:
    feed = KrakenCSVFeed(data_dir=KRACKEN_DATA_DIR, interval=timeframe)
    try:
        df = feed.get_data(symbol)
        return df.index[0].to_pydatetime(), df.index[-1].to_pydatetime()
    except Exception:
        return datetime(2020, 1, 1), datetime.now()


def load_ohlcv_data(
    symbol: str,
    timeframe: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days: Optional[int] = None,
) -> pd.DataFrame:
    feed = KrakenCSVFeed(data_dir=KRACKEN_DATA_DIR, interval=timeframe)
    return feed.get_data(symbol, start_date, end_date)


def get_data_info(df: pd.DataFrame) -> dict:
    return {
        'rows': len(df),
        'start': df.index[0] if len(df) > 0 else None,
        'end': df.index[-1] if len(df) > 0 else None,
        'columns': list(df.columns),
    }