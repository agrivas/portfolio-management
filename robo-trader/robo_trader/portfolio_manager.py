# robo_trader/portfolio_manager.py

import json
import pandas as pd
from datetime import datetime
from robo_trader.types import TradeAction, Ohlcv

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class PortfolioManager:
    def __init__(self,
                 symbol: str,
                 inception_date: datetime = datetime.now(),
                 initial_cash: float = 1000.0,
                 initial_tokens: float = 0,
                 transaction_costs: float = 0.004,
                 stop_loss_percentage: float = 0.1,
                 cash_reserve_percentage: float = .5):
        self.symbol = symbol
        self.initial_cash = initial_cash
        self.initial_tokens = initial_tokens
        self.transaction_costs = transaction_costs
        self.stop_loss_percentage = stop_loss_percentage
        self.cash_reserve_percentage = cash_reserve_percentage
        self.cash = initial_cash
        self.tokens = initial_tokens
        self.inception_date = inception_date
        
        self.trades = []  # List to keep track of all trades
        self.filename = f'portfolio_{symbol}_{inception_date.strftime(DATE_FORMAT)}.json'

        self.save_state()

    @classmethod
    def from_file(cls, filename: str):
        obj = cls('DUMMY')
        obj.load_state(filename)
        return obj

    def buy(self, price_override: float = None, date_override: datetime = None):
        # Calculate trade amount based on available cash and bet percentage
        current_price = self.get_current_price(price_override)
        trade_amount = self.cash / (current_price * (1 + self.transaction_costs))

        # Buy tokens using available cash
        self.execute_trade(TradeAction.BUY, trade_amount, price_override, date_override)

    def sell(self, price_override: float = None, date_override: datetime = None):
        # Calculate trade amount based on current holdings and cash reserve percentage
        if self.tokens > 0:
            # Calculate the current value of the asset
            current_asset_value = self.tokens * self.get_current_price(price_override)

            # Calculate the cash reserve required based on cash_reserve_percentage
            cash_reserve_required = (self.cash + current_asset_value) * self.cash_reserve_percentage

            # Check if selling the entire asset is necessary to restore cash reserve
            if self.cash < cash_reserve_required:
                # Sell only the required amount to restore cash reserve
                residual_holding = self.tokens - ((cash_reserve_required - self.cash) / self.get_current_price(price_override))
                trade_amount = self.tokens - residual_holding
            else:
                # Sell all of the asset
                trade_amount = self.tokens

            # Ensure trade amount is not negative
            trade_amount = max(trade_amount, 0)

            if trade_amount > 0:
                # Sell tokens
                self.execute_trade(TradeAction.SELL, trade_amount, price_override, date_override)

    def get_current_price(self, override: float = None):
        # When back-testing the expected price is fed in externally
        if override is not None:
            return override
        
        # TODO: Get price from API
        return 100

    def get_date(self, override: datetime = None):
        # When back-testing the expected date is fed in externally
        if override is not None:
            return override
        
        # Get current date
        return datetime.now()
    
    def calculate_trade_cost(self, trade_amount: float, price_override: float = None):
        # Get the cost of a transaction
        current_price = self.get_current_price(price_override)
        return current_price * trade_amount * self.transaction_costs

    def execute_trade(self, action: str, trade_amount: float, price_override: float, date_override: datetime = None):
        # Record the trade
        price = self.get_current_price(price_override)
        trade_date = self.get_date(date_override)
        cost = self.calculate_trade_cost(trade_amount, price_override)
        
        cash_value = price * trade_amount
        
        if action == TradeAction.BUY:
            if self.cash < cash_value + cost:
                raise ValueError("Not enough cash")

            self.cash -= (cash_value + cost) 
            self.tokens += trade_amount
        elif action == TradeAction.SELL:
            if self.tokens < trade_amount:
                raise ValueError("Not enough tokens")

            self.cash += (cash_value - cost)
            self.tokens -= trade_amount

        self.trades.append({
            'action': action,
            'trade_amount': trade_amount,
            'price': price,
            'date': trade_date.strftime(DATE_FORMAT),
            'cost': cost,
            'current_tokens': self.tokens,
            'current_cash': self.cash
        })

        self.save_state()        

    def get_portfolio_value(self, price_override: float = None):
        # Calculate the total value of the portfolio using the provided price override if available
        current_price = self.get_current_price(price_override)
        return self.cash + (self.tokens * current_price)

    def calculate_performance(self, period: pd.DataFrame):
        # Calculate the performance of the portfolio
        
        if period.empty:
            return 0
        
        start_date = period.index[0]
        end_date = period.index[-1]

        if end_date < self.inception_date or start_date > datetime.now():
            return 0

        current_cash = self.initial_cash
        current_tokens = self.initial_tokens      

        # Find the last trade before the period starts
        last_trade_before_period = next((trade for trade in reversed(self.trades) if datetime.strptime(trade['date'], DATE_FORMAT) < start_date), None)
        if last_trade_before_period is not None:
            current_tokens, current_cash = last_trade_before_period['current_tokens'], last_trade_before_period['current_cash']

        # Calculate portfolio value at the start of the period
        opening_price = period.iloc[0][Ohlcv.OPEN]
        start_value = current_cash + (current_tokens * opening_price)

        # Find the last trade within the period
        last_trade_within_period = next((trade for trade in reversed(self.trades) if datetime.strptime(trade['date'], DATE_FORMAT) <= end_date), None)
        if last_trade_within_period is not None:
            current_tokens, current_cash = last_trade_within_period['current_tokens'], last_trade_within_period['current_cash']

        # Calculate portfolio value at the end of the period
        closing_price = period.iloc[-1][Ohlcv.CLOSE]
        end_value = current_cash + (current_tokens * closing_price)

        # Calculate performance
        performance = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0

        return performance
    
    def save_state(self, filename: str = None):
        file = filename if filename is not None else self.filename

        # Save the current state of the portfolio manager to disk
        state = {
            'symbol': self.symbol,
            'initial_cash': self.initial_cash,
            'initial_tokens': self.initial_tokens,
            'transaction_costs': self.transaction_costs,
            'stop_loss_percentage': self.stop_loss_percentage,
            'cash_reserve_percentage': self.cash_reserve_percentage,
            'cash': self.cash,
            'tokens': self.tokens,
            'inception_date': self.inception_date.strftime(DATE_FORMAT),
            'trades': self.trades,
            'filename': self.filename,
        }
        with open(file, 'w') as f:
            json.dump(state, f)

    def load_state(self, filename: str = None):
        file = filename if filename is not None else self.filename

        # Load the saved state of the portfolio manager from disk if available
        try:
            with open(file, 'r') as f:
                saved_state = json.load(f)
                self.symbol = saved_state['symbol']
                self.initial_cash = saved_state['initial_cash']
                self.initial_tokens = saved_state['initial_tokens']
                self.transaction_costs = saved_state['transaction_costs']
                self.stop_loss_percentage = saved_state['stop_loss_percentage']
                self.cash_reserve_percentage = saved_state['cash_reserve_percentage']
                self.cash = saved_state['cash']
                self.tokens = saved_state['tokens']
                self.inception_date = datetime.strptime(saved_state['inception_date'], DATE_FORMAT)
                self.trades = saved_state['trades']
                self.filename = saved_state['filename']

        except FileNotFoundError:
            pass
        
    def __str__(self):
        return f"Cash: {self.cash}, Tokens: {self.tokens}, Trades: {self.trades}"
