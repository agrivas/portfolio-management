import time
import signal
from datetime import datetime
import pandas as pd
import numpy as np
from .feed import Feed
from .strategy import Strategy
from .portfolio import Portfolio
from .broker import Broker, OrderSide, OrderType
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
            self.portfolio.update()  # Update portfolio in every iteration
            
            current_data = self.feed.get_live_data(self.symbol)
            if not current_data.empty and (self.last_data_timestamp is None or current_data['date'].max() > self.last_data_timestamp):
                self.last_data_timestamp = current_data['date'].max()
                self.strategy.evaluate_market(self)
            
            time.sleep(60)  # Sleep for a minute

    def backtest(self, start_date: datetime = None, end_date: datetime = None, period: int = None, train_since: datetime = None):
        """
        Replay historical data from the price provider as if we received one point at a time.
        Track the price of the asset on the first date and the valuation of the portfolio.
        Record them again at the end of the period, calculate the returns for both and return them in a unified dataframe.
        Additionally, calculate discrete performance every 'period' prices if specified, including a row for the whole period.
        """
        backtest_broker = BacktestBroker()
        backtest_portfolio = Portfolio(backtest_broker, self.initial_cash)

        if train_since and start_date and train_since >= start_date:
            raise ValueError("train_since must be before start_date")

        prices_since = None
        if train_since:
            prices_since = train_since
        elif start_date:
            prices_since = start_date

        prices = self.feed.get_historical_data(self.symbol, prices_since, end_date)
        if prices.empty:
            print("No historical data available for backtesting.")
            return

        start_index = prices.index.get_loc(start_date) if start_date else 0
        initial_price = prices.iloc[start_index]['open']
        initial_date = prices.index[start_index]
        initial_portfolio_valuation = backtest_portfolio.get_valuation(time=initial_date, prices={self.symbol: initial_price})

        returns_data = []
        last_discrete_price = initial_price
        last_discrete_portfolio_valuation = initial_portfolio_valuation

        # Add columns for tracking long positions
        prices['open_long'] = False
        prices['close_long'] = False

        # For tracking wins and losses
        wins = 0
        total_trades = 0
        portfolio_returns = []
        asset_returns = []

        # Iterate from start_index to the end of the frame
        for index in range(start_index, len(prices)):
            price_point = prices.iloc[index]
            self.last_price_point = price_point

            # Update backtest broker with current price and timestamp
            backtest_broker.set_timestamp(index)
            backtest_broker.set_price(self.symbol, price_point['close'])
            
            # Update portfolio before strategy evaluation
            backtest_portfolio.update()

            # Store the portfolio state before strategy evaluation
            prev_holdings = backtest_portfolio.asset_holdings.get(self.symbol, 0)
            prev_portfolio_value = backtest_portfolio.get_valuation(time=prices.index[index], prices={self.symbol: price_point['close']})

            # Call evaluate_market on the strategy with prices up to the current index and the trader
            self.strategy.evaluate_market(prices.iloc[:index+1], self)

            # Check if a long position was opened or closed
            current_holdings = backtest_portfolio.asset_holdings.get(self.symbol, 0)
            if current_holdings > prev_holdings:
                prices.at[price_point.name, 'open_long'] = True
            elif current_holdings < prev_holdings:
                prices.at[price_point.name, 'close_long'] = True
                total_trades += 1
                current_portfolio_value = backtest_portfolio.get_valuation(time=prices.index[index], prices={self.symbol: price_point['close']})
                if current_portfolio_value > prev_portfolio_value:
                    wins += 1

            # Calculate returns
            if index > start_index:
                portfolio_return = (backtest_portfolio.get_valuation(time=prices.index[index], prices={self.symbol: price_point['close']}) - 
                                    backtest_portfolio.get_valuation(time=prices.index[index-1], prices={self.symbol: prices.iloc[index-1]['close']})) / \
                                   backtest_portfolio.get_valuation(time=prices.index[index-1], prices={self.symbol: prices.iloc[index-1]['close']})
                asset_return = (price_point['close'] - prices.iloc[index-1]['close']) / prices.iloc[index-1]['close']
                
                portfolio_returns.append(portfolio_return)
                asset_returns.append(asset_return)

            # Check if we should record the data
            if (period is not None and (index - start_index) % period == 0):
                current_price = price_point['close']
                current_date = prices.index[index]
                current_portfolio_valuation = backtest_portfolio.get_valuation(time=current_date, prices={self.symbol: current_price})
                price_return = (current_price - last_discrete_price) / last_discrete_price
                portfolio_return = (current_portfolio_valuation - last_discrete_portfolio_valuation) / last_discrete_portfolio_valuation

                returns_data.append({
                    'start_date': prices.index[max(start_index, index - period)],
                    'end_date': current_date,
                    'price_start': last_discrete_price,
                    'price_end': current_price,                    
                    'valuation_start': last_discrete_portfolio_valuation,
                    'valuation_end': current_portfolio_valuation,
                    'asset_return': price_return,
                    'portfolio_return': portfolio_return
                })

                last_discrete_price = current_price
                last_discrete_portfolio_valuation = current_portfolio_valuation

        # Add row for the whole period
        final_price = prices.iloc[-1]['close']
        final_date = prices.index[-1]
        final_portfolio_valuation = backtest_portfolio.get_valuation(time=final_date, prices={self.symbol: final_price})
        total_price_return = (final_price - initial_price) / initial_price
        total_portfolio_return = (final_portfolio_valuation - initial_portfolio_valuation) / initial_portfolio_valuation

        returns_data.append({
            'start_date': initial_date,
            'end_date': final_date,
            'price_start': initial_price,
            'price_end': final_price,            
            'valuation_start': initial_portfolio_valuation,
            'valuation_end': final_portfolio_valuation,
            'asset_return': total_price_return,
            'portfolio_return': total_portfolio_return
        })

        returns = pd.DataFrame(returns_data)

        # Calculate performance stats
        win_rate = wins / total_trades if total_trades > 0 else 0
        portfolio_returns = np.array(portfolio_returns)
        asset_returns = np.array(asset_returns)
        excess_returns = portfolio_returns - asset_returns
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else 0
        downside_returns = np.minimum(excess_returns - 0, 0)
        sortino_ratio = np.mean(excess_returns) / np.std(downside_returns) if np.std(downside_returns) != 0 else 0

        performance_stats = {
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio
        }

        return returns, prices, performance_stats
