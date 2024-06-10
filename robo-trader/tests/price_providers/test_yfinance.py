import unittest
from datetime import datetime, timedelta, timezone
from robo_trader.price_providers.yfinance import YFinancePriceProvider
from robo_trader.price_provider import Interval
import pandas as pd
from zoneinfo import ZoneInfo

class TestYFinancePriceProvider(unittest.TestCase):
    def setUp(self):
        self.provider = YFinancePriceProvider()

    def test_get_prices_with_default_dates(self):
        """ Test fetching prices with default dates (maximum period) """
        symbol = "AAPL"
        interval = Interval.ONE_DAY
        df = self.provider.get_prices(symbol, interval)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)

    def test_get_prices_with_specific_dates(self):
        """Test fetching prices with specific start and end dates."""
        symbol = "BTC-GBP"
        interval = Interval.ONE_HOUR
        start_date = (datetime.now(timezone.utc) - timedelta(days=366)).replace(minute=0, second=0, microsecond=0)
        end_date = (datetime.now(timezone.utc) - timedelta(days=365)).replace(minute=0, second=0, microsecond=0)
        df = self.provider.get_prices(symbol, interval, start_date, end_date)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertTrue(
            df.index.min().astimezone(ZoneInfo("UTC")) >= pd.to_datetime(start_date) and 
            df.index.max().astimezone(ZoneInfo("UTC")) <= pd.to_datetime(end_date)
        )

if __name__ == '__main__':
    unittest.main()
