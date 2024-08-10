import yfinance
from datetime import datetime
from robo_trader.feed import Feed, Ohlcv
import pandas as pd

class YFinanceFeed(Feed):
    def __init__(self, interval: str = '1d', invert_pair: bool = False):
        self.interval = interval
        self.invert_pair = invert_pair
    
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
        df = ticker_data.history(interval=self.interval, period="1d")  # Changed to "1d" to get the latest data
        
        return self._format_dataframe(df)

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Ensure the index is a DatetimeIndex and convert to UTC
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index.tz_convert('UTC')
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

        if self.invert_pair:
            # Invert the price columns (Open, High, Low, Close)
            for col in [Ohlcv.OPEN, Ohlcv.HIGH, Ohlcv.LOW, Ohlcv.CLOSE]:
                df[col] = 1 / df[col]
            
            # Adjust the volume
            df[Ohlcv.VOLUME] = df[Ohlcv.VOLUME] * df[Ohlcv.CLOSE]
            
            # Swap High and Low
            df[Ohlcv.HIGH], df[Ohlcv.LOW] = 1 / df[Ohlcv.LOW], 1 / df[Ohlcv.HIGH]

        return df
