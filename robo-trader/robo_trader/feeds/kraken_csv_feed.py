import pandas as pd
from datetime import datetime
from robo_trader.feed import Feed, Ohlcv
import os

class KrakenCSVFeed(Feed):
    def __init__(self, data_dir: str, interval: str = '15m'):
        self.data_dir = data_dir
        self.interval = interval
        
        self.interval_map = {
            '1m': '1',
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '4h': '240',
            '12h': '720',
            '1d': '1440',
        }

    def get_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        tf = self.interval_map.get(self.interval, '15')
        
        # Convert BTC to XBT for Kraken naming convention
        kraken_symbol = symbol.replace('BTC', 'XBT').replace('/', '').replace('-', '')
        
        filepath = os.path.join(self.data_dir, f"{kraken_symbol}_{tf}.csv")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"OHLCV file not found: {filepath}")
        
        df = pd.read_csv(
            filepath,
            names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades']
        )
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s').dt.tz_localize('UTC')
        
        if start_date is not None:
            if isinstance(start_date, datetime):
                start_date = pd.Timestamp(start_date)
            if start_date.tzinfo is None:
                start_date = start_date.tz_localize('UTC')
            df = df[df['timestamp'] >= start_date]
        
        if end_date is not None:
            if isinstance(end_date, datetime):
                end_date = pd.Timestamp(end_date)
            if end_date.tzinfo is None:
                end_date = end_date.tz_localize('UTC')
            df = df[df['timestamp'] <= end_date]
        
        df = df.rename(columns={
            'timestamp': Ohlcv.DATE,
            'open': Ohlcv.OPEN,
            'high': Ohlcv.HIGH,
            'low': Ohlcv.LOW,
            'close': Ohlcv.CLOSE,
            'volume': Ohlcv.VOLUME
        })
        
        df = df[[Ohlcv.DATE, Ohlcv.OPEN, Ohlcv.HIGH, Ohlcv.LOW, Ohlcv.CLOSE, Ohlcv.VOLUME]]
        
        df = df.set_index(Ohlcv.DATE)
        
        return df