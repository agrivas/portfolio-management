import yfinance
from datetime import datetime
from ..feed import Feed, Ohlcv
import pandas as pd

class YFinanceFeed(Feed):
    def __init__(self, interval: str = '1d'):
        self.interval = interval
    
    def get_historical_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        period = None
        if start_date is None and end_date is None:
            period = 'max'

        ticker_data = yfinance.Ticker(symbol)

        if period is not None:
            df = ticker_data.history(interval=self.interval, period=period)
        else:            
            df = ticker_data.history(interval=self.interval, start=start_date, end=end_date)

        return self._format_dataframe(df)

    def get_live_data(self, symbol: str) -> pd.DataFrame:
        ticker_data = yfinance.Ticker(symbol)
        
        # Get the most recent data point
        df = ticker_data.history(interval=self.interval, period="max")
        
        return self._format_dataframe(df)

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Rename index to match Ohlcv.DATE and make timezone aware on UTC
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = df.index.tz_convert('UTC')
        df.index.names = [Ohlcv.DATE]

        # Rename columns to match Ohlcv enum types
        new_names = {
            'Open': Ohlcv.OPEN,
            'High': Ohlcv.HIGH,
            'Low': Ohlcv.LOW,
            'Close': Ohlcv.CLOSE,
            'Volume': Ohlcv.VOLUME
        }
        df = df.rename(columns=new_names)

        return df


