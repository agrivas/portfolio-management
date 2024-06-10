import yfinance
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from robo_trader.price_provider import PriceProvider
from robo_trader.types import Ohlcv
from robo_trader.price_provider import Interval
import pandas as pd

class YFinancePriceProvider(PriceProvider):
    def get_prices(self, symbol: str, interval: Interval, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        period = None
        if start_date is None and end_date is None:
            period = 'max'

        ticker_data = yfinance.Ticker(symbol)
        yfinance_interval = self.map_interval_to_yfinance(interval)

        if period is not None:
            df = ticker_data.history(interval=yfinance_interval, period=period)
        else:            
            df = ticker_data.history(interval=yfinance_interval, start=start_date, end=end_date)

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

    def map_interval_to_yfinance(self, interval: Interval) -> str:
        """
        Maps the internal Interval enum to the format expected by yfinance.

        :param interval: Interval enum from the internal system.
        :return: A string representing the interval in yfinance format.
        """
        interval_mapping = {
            Interval.ONE_MINUTE: '1m',
            Interval.FIVE_MINUTES: '5m',
            Interval.FIFTEEN_MINUTES: '15m',
            Interval.THIRTY_MINUTES: '30m',
            Interval.ONE_HOUR: '1h',
            Interval.ONE_DAY: '1d',
            Interval.ONE_WEEK: '1wk',
            Interval.ONE_MONTH: '1mo',
        }
        return interval_mapping.get(interval, '1d')  # Default to '1d' if not found


