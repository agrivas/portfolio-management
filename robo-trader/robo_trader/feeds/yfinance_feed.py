import yfinance
from datetime import datetime, timedelta
from robo_trader.feed import Feed, Ohlcv
import pandas as pd

class YFinanceFeed(Feed):
    def __init__(self, interval: str = '1d', invert_pair: bool = False, default_period: timedelta = timedelta(days=365)):
        self.interval = interval
        self.invert_pair = invert_pair
        self.default_period = default_period
    
    def get_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        ticker_data = yfinance.Ticker(symbol)

        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            start_date = end_date - self.default_period

        df = ticker_data.history(interval=self.interval, start=start_date, end=end_date)
        
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
