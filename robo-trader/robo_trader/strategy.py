from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
from enum import Enum
import random
from robo_trader.portfolio import Portfolio
from robo_trader.price_provider import PriceProvider, Interval

class TradeSignal(Enum):
    BUY = 'Buy'
    SELL = 'Sell'
    REBALANCE = 'Rebalance'
    NO_ACTION = 'No Action'

class Strategy(ABC):
    def __init__(self, symbol: str, price_provider: PriceProvider, interval: Interval, portfolio: Portfolio):
        self.symbol = symbol
        self.price_provider = price_provider
        self.portfolio = portfolio
        self.interval = interval

    def backtest(self, start_date: datetime = None, end_date: datetime = None, period: int = None, train_since: datetime = None):
        """
        Replay historical data from the price provider as if we received one point at a time.
        Track the price of the asset on the first date and the valuation of the portfolio.
        Record them again at the end of the period, calculate the returns for both and return them in a unified dataframe.
        Additionally, calculate discrete performance every 'period' prices if specified, including a row for the whole period.
        """
        if train_since and start_date and train_since >= start_date:
            raise ValueError("train_since must be before start_date")

        prices_since = None
        if train_since:
            prices_since = train_since
        elif start_date:
            prices_since = start_date

        prices = self.price_provider.get_prices(self.symbol, self.interval, prices_since, end_date)
        if prices.empty:
            print("No historical data available for backtesting.")
            return

        start_index = prices.index.get_loc(start_date)
        initial_price = prices.iloc[start_index]['open']
        initial_date = prices.index[start_index]
        initial_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=initial_price, valuation_point=initial_date)

        returns_data = []
        last_discrete_price = initial_price
        last_discrete_portfolio_valuation = initial_portfolio_valuation

        # Iterate from start_index to the end of the frame
        for index in range(start_index, len(prices)):
            price_point = prices.iloc[index]
            self.last_price_point = price_point

            # Pass the frame from the beginning up to the current index (inclusive) to backtest_evaluate_market
            self.backtest_evaluate_market(prices.iloc[:index+1])

            # Check if we should record the data
            if (period is not None and (index - start_index) % period == 0):
                current_price = price_point['close']
                current_date = prices.index[index]
                current_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=current_price, valuation_point=current_date)
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
        final_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=final_price, valuation_point=final_date)
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

        returns_df = pd.DataFrame(returns_data)
        
        performance_filename = f'performance_{self.interval.value}_{period}_{self.portfolio.filename.replace(".json", "")}.csv'
        returns_df.to_csv(performance_filename, index=False)

        return returns_df

    def backtest_evaluate_market(self, prices):
        """
        Evaluate the market conditions based on Lorentzian analysis and decide whether to buy, sell, or rebalance.
        """
        market_condition = self.analyze_prices(prices)

        latest_close_price = prices.iloc[-1]['close']
        latest_date = prices.index[-1]

        if market_condition == TradeSignal.BUY:
            self.portfolio.backtest_buy(latest_close_price, latest_date)
        elif market_condition == TradeSignal.SELL:
            self.portfolio.backtest_sell(latest_close_price, latest_date)
        elif market_condition == TradeSignal.REBALANCE:
            self.portfolio.backtest_rebalance(latest_close_price, latest_date)

        self.last_prediction = market_condition

    def run(self):
        """
        Continuously evaluate the market at every minute, only if new data is available.
        """
        import time
        try:
            while True:
                prices = self.price_provider.get_prices(self.symbol, self.interval)
                if prices.empty or (self.last_price_point is not None and prices.iloc[-1].equals(self.last_price_point)):
                    print("No new data. Waiting for next interval.")
                else:
                    self.last_price_point = prices.iloc[-1]
                    self.evaluate_market(prices)
                time.sleep(60)  # Sleep for 60 seconds before the next evaluation
        except KeyboardInterrupt:
            print("Stopped the market evaluation loop.")

    def evaluate_market(self, prices):
        """
        Evaluate the market conditions based on Lorentzian analysis and decide whether to buy, sell, or rebalance.
        """
        market_condition = self.analyze_prices(prices)
                
        if market_condition == TradeSignal.BUY:
            self.portfolio.buy()
        elif market_condition == TradeSignal.SELL:
            self.portfolio.sell()
        elif market_condition == TradeSignal.REBALANCE:
            self.portfolio.rebalance()

        self.last_prediction = market_condition

    @abstractmethod
    def analyze_prices(self, prices):
        pass

class DummyStrategy(Strategy):
    def analyze_prices(self, prices):
        """
        Randomly decide to buy, sell, or rebalance.
        """
        return random.choice(list(TradeSignal))
