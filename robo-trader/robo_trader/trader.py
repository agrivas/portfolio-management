import time
import signal
from datetime import datetime
from .feed import Feed
from .strategy import Strategy
from .portfolio import Portfolio
from .broker import Broker
from .brokers.backtest_broker import BacktestBroker

class Trader:
    def __init__(self, symbol: str, initial_cash: float, feed: Feed, strategy: Strategy, broker: Broker = None):
        self.symbol = symbol
        self.feed = feed
        self.strategy = strategy
        self.broker = broker
        self.initial_cash = initial_cash
        self.portfolio = Portfolio(broker, initial_cash) if broker else None
        self.last_data_timestamp = None

    def run(self):
        """
        Handle live trading by continuously processing the feed and executing trades through the portfolio.
        This method runs every minute and evaluates the market if new data has been received.
        It also allows for an exit option by handling a SIGINT (Ctrl+C).
        """
        if not self.broker:
            raise ValueError("Cannot run live trading without a broker. Please provide a broker instance.")

        def signal_handler(sig, frame):
            print("Exiting trading loop.")
            exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while True:
            current_data = self.feed.get_data(self.symbol)
            if not current_data.empty:
                if (self.last_data_timestamp is None or current_data['date'].max() > self.last_data_timestamp):
                    self.last_data_timestamp = current_data['date'].max()
                    self.strategy.evaluate_market(self, current_data, self.portfolio)
                    self.portfolio.update(self.last_data_timestamp, {self.symbol: current_data['close'].iloc[-1]})
            
            time.sleep(60)  # Sleep for a minute

    def backtest(self, start_date: datetime = None, end_date: datetime = None, period: int = None, train_since: datetime = None, transaction_cost: float = None, trailing_stop_penalty_relief: float = None):
        """
        Replay historical data from the price provider as if we received one point at a time.
        Track the price of the asset on the first date and the valuation of the portfolio.
        Record them again at the end of the period, calculate the returns for both and return them in a unified dataframe.
        Additionally, calculate discrete performance every 'period' prices if specified, including a row for the whole period.
        """
        backtest_broker = BacktestBroker(transaction_cost if transaction_cost is not None else 0, trailing_stop_penalty_relief if trailing_stop_penalty_relief is not None else 0.75)
        backtest_portfolio = Portfolio(backtest_broker, self.initial_cash, autosave=False)

        if train_since and start_date and train_since >= start_date:
            raise ValueError("train_since must be before start_date")

        prices_since = train_since if train_since else start_date

        prices = self.feed.get_data(self.symbol, prices_since, end_date)
        if prices.empty:
            print("No historical data available for backtesting.")
            return

        start_index = prices.index.get_loc(prices.index.asof(start_date)) if start_date else 0

        # Iterate from start_index to the end of the frame
        for index in range(start_index, len(prices)):
            price_point = prices.iloc[index]

            # Update backtest broker with current price and timestamp
            backtest_broker.update(prices.index[index], {self.symbol: price_point['close']})
                        
            # Call evaluate_market on the strategy with prices up to the current index and the trader
            self.strategy.evaluate_market(self.symbol, prices.iloc[:index+1], backtest_portfolio)

            # Update portfolio after strategy evaluation
            backtest_portfolio.update(prices.index[index], {self.symbol: price_point['close']})

        backtest_portfolio.save()

        return backtest_portfolio