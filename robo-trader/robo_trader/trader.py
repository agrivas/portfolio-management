import time
import signal
from datetime import datetime
import pandas as pd
import numpy as np
from .feed import Feed
from .strategy import Strategy
from .portfolio import Portfolio
from .broker import Broker, OrderStatus, OrderSide
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
            current_data = self.feed.get_live_data(self.symbol)
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

        prices_since = None
        if train_since:
            prices_since = train_since
        elif start_date:
            prices_since = start_date

        prices = self.feed.get_historical_data(self.symbol, prices_since, end_date)
        if prices.empty:
            print("No historical data available for backtesting.")
            return

        start_index = prices.index.get_loc(prices.index.asof(start_date)) if start_date else 0
        initial_price = prices.iloc[start_index]['open']
        initial_date = prices.index[start_index]
        initial_portfolio_valuation = backtest_portfolio.get_valuation(time=initial_date, prices={self.symbol: initial_price})

        returns_data = []
        last_discrete_price = initial_price
        last_discrete_portfolio_valuation = initial_portfolio_valuation

        # Add columns for tracking long positions
        prices['open_long'] = False
        prices['close_long'] = False

        # Iterate from start_index to the end of the frame
        for index in range(start_index, len(prices)):
            price_point = prices.iloc[index]

            # Store the portfolio state before strategy evaluation
            prev_holdings = backtest_portfolio.asset_holdings.get(self.symbol, 0)
            prev_portfolio_value = backtest_portfolio.get_valuation(time=prices.index[index], prices={self.symbol: price_point['close']})

            # Update backtest broker with current price and timestamp
            backtest_broker.set_timestamp(prices.index[index])
            backtest_broker.set_price(self.symbol, price_point['close'])
            backtest_broker.update()
                        
            # Call evaluate_market on the strategy with prices up to the current index and the trader
            self.strategy.evaluate_market(self.symbol, prices.iloc[:index+1], backtest_portfolio)

            # Update portfolio after strategy evaluation
            backtest_portfolio.update(prices.index[index], {self.symbol: price_point['close']})

            # Check if a long position was opened or closed
            current_holdings = backtest_portfolio.asset_holdings.get(self.symbol, 0)
            if current_holdings > prev_holdings:
                prices.at[prices.index[index], 'open_long'] = True
            elif current_holdings < prev_holdings:
                prices.at[prices.index[index], 'close_long'] = True

            # Check if we should record the data
            if (period is not None and (index - start_index) % period == 0 and (index - start_index) / period > 0):
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

        backtest_portfolio.save()

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

        # Calculate win_rate based on trades
        winning_trades = 0
        total_trades = 0
        open_position = None
        for order in backtest_portfolio.orders.values():
            if order.status == OrderStatus.FILLED and order.trades:
                if order.order_side == OrderSide.BUY:
                    # Open a new position
                    open_position = {
                        'buy_cash': sum((trade.price * trade.quantity + trade.transaction_costs) for trade in order.trades),
                        'quantity': sum(trade.quantity for trade in order.trades),
                        'symbol': order.symbol
                    }
                elif order.order_side == OrderSide.SELL and open_position and order.symbol == open_position['symbol']:
                    # Close the position
                    total_trades += 1
                    sell_cash = sum((trade.price * trade.quantity - trade.transaction_costs) for trade in order.trades)
                    
                    # Compare sell cash to buy cash
                    if sell_cash > open_position['buy_cash']:
                        winning_trades += 1
                    
                    # Reset open position
                    open_position = None

        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        performance_stats = {
            'initial_value': initial_portfolio_valuation,
            'final_value': final_portfolio_valuation,
            'win_rate': win_rate,
            'history': prices,
            'returns': returns,
            'orders': backtest_portfolio.orders
        }

        return performance_stats
