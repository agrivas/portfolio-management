import ccxt
import pandas as pd
from datetime import datetime, timedelta
from robo_trader.feed import Feed, Ohlcv

class CCXTFeed(Feed):
    def __init__(self, exchange_id: str, api_key: str = '', secret: str = '', interval: str = '1d', invert_pair: bool = False, default_period: timedelta = timedelta(days=365)):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })
        self.interval = interval
        self.invert_pair = invert_pair
        self.default_period = default_period

    def get_data(self, symbol: str, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        try:
            if end_date is None:
                end_date = datetime.now()

            if start_date is None:
                start_date = end_date - self.default_period

            timeframe = self.interval
            since = int(start_date.timestamp() * 1000)
            end = int(end_date.timestamp() * 1000)
            
            all_ohlcv = []
            while True:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since)
                if len(ohlcv) == 0:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                if since >= end:
                    break

            df = pd.DataFrame(all_ohlcv, columns=[Ohlcv.DATE, Ohlcv.OPEN, Ohlcv.HIGH, Ohlcv.LOW, Ohlcv.CLOSE, Ohlcv.VOLUME])
            df[Ohlcv.DATE] = pd.to_datetime(df[Ohlcv.DATE], unit='ms').dt.tz_localize('UTC')
            
            if len(df) > 0 and end_date is not None:
                if isinstance(end_date, datetime):
                    end_date = pd.Timestamp(end_date)
                if end_date.tzinfo is None:
                    end_date = end_date.tz_localize('UTC')
                df = df[df[Ohlcv.DATE] <= end_date]

            df.set_index(Ohlcv.DATE, inplace=True)
            
            if self.invert_pair:
                for col in [Ohlcv.OPEN, Ohlcv.HIGH, Ohlcv.LOW, Ohlcv.CLOSE]:
                    df[col] = 1 / df[col]
                df[Ohlcv.VOLUME] = df[Ohlcv.VOLUME] * df[Ohlcv.CLOSE]
                df[Ohlcv.HIGH], df[Ohlcv.LOW] = 1 / df[Ohlcv.LOW], 1 / df[Ohlcv.HIGH]
            
            return df

        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")