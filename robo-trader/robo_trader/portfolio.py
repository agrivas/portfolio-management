# robo_trader/portfolio.py

import json
from datetime import datetime, timezone
from .types import TradeAction
from .exchange import Exchange, DummyExchange

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class Portfolio:
    def __init__(self,
                 symbol: str,
                 exchange: Exchange,
                 inception_date: datetime = datetime.now(timezone.utc),
                 initial_cash: float = 1000.0,
                 initial_tokens: float = 0,
                 transaction_costs: float = 0.004,
                 stop_loss_percentage: float = 0.1,
                 cash_reserve_percentage: float = .5,
                 minimum_cash_reserve: float = 10.0):
        self.symbol = symbol
        self.exchange = exchange
        self.initial_cash = initial_cash
        self.initial_tokens = initial_tokens
        self.transaction_costs = transaction_costs
        self.stop_loss_percentage = stop_loss_percentage
        self.cash_reserve_percentage = cash_reserve_percentage
        self.cash = initial_cash
        self.tokens = initial_tokens
        self.inception_date = inception_date
        self.minimum_cash_reserve = minimum_cash_reserve
        
        self.trades = []  # List to keep track of all trades
        self.filename = f'portfolio_{symbol}_{inception_date.strftime(DATE_FORMAT)}.json'

        self.save_state()

    @classmethod
    def from_file(cls, filename: str):
        obj = cls('DUMMY', DummyExchange())
        obj.load_state(filename)
        return obj

    def calculate_amount_to_buy(self, price: float):
        # keep a minimum cash reserve
        return (self.cash - self.minimum_cash_reserve) / (price * (1 + self.transaction_costs))

    def buy(self):
        price = self.get_current_price()
        trade_amount = self.calculate_amount_to_buy(price)

        if trade_amount > 0:
            exchange_trade = self.exchange.execute_trade(self.symbol, TradeAction.BUY, trade_amount)
            
            if exchange_trade.success:
                # record the trade
                self.record_trade(TradeAction.BUY, exchange_trade.trade_amount, exchange_trade.price, exchange_trade.date, exchange_trade.cost)

    def calculate_amount_to_sell(self, price: float):
        # Sell all the tokens if any are available
        return max(self.tokens, 0)

    def sell(self):
        price = self.get_current_price()
        trade_amount = self.calculate_amount_to_sell(price)

        if trade_amount > 0:
            exchange_trade = self.exchange.execute_trade(self.symbol, TradeAction.SELL, trade_amount)
            
            if exchange_trade.success:
                # record the trade
                self.record_trade(TradeAction.SELL, exchange_trade.trade_amount, exchange_trade.price, exchange_trade.date, exchange_trade.cost)

    def calculate_trade_action_to_rebalance(self, price: float):
        # Calculate the total value of the portfolio (cash + value of tokens)
        total_value = self.cash + (self.tokens * price)
        
        # Calculate the target cash reserve based on the total value and the cash reserve percentage
        target_cash_reserve = (total_value - self.minimum_cash_reserve) * self.cash_reserve_percentage
        
        # Determine the amount of cash needed to reach the target cash reserve
        cash_needed_to_rebalance = target_cash_reserve - self.cash
        
        # If the cash needed to rebalance is less than the minimum cash reserve, do not rebalance
        if abs(cash_needed_to_rebalance) < self.minimum_cash_reserve:
            return None, 0
        
        # Calculate the amount of tokens to buy or sell to rebalance the cash reserve
        if cash_needed_to_rebalance > 0:
            # Need to sell tokens to increase cash
            amount_to_trade = cash_needed_to_rebalance / (price * (1 + self.transaction_costs))
            trade_action = TradeAction.SELL
        else:
            # Need to buy tokens to decrease cash
            amount_to_trade = -cash_needed_to_rebalance / (price * (1 + self.transaction_costs))
            trade_action = TradeAction.BUY
        
        # Ensure the trade amount is not negative and does not exceed the tokens available if selling
        amount_to_trade = max(min(amount_to_trade, self.tokens if trade_action == 'SELL' else float('inf')), 0)
        
        return trade_action, amount_to_trade

    def rebalance(self):
        price = self.get_current_price()
        trade_action, amount_to_trade = self.calculate_trade_action_to_rebalance(price)

        if amount_to_trade > 0 and trade_action is not None:
            exchange_trade = self.exchange.execute_trade(self.symbol, trade_action, amount_to_trade)
            
            if exchange_trade.success:
                # record the trade
                self.record_trade(trade_action, exchange_trade.trade_amount, exchange_trade.price, exchange_trade.date, exchange_trade.cost)
        else:
            print("No trade needed for rebalancing.")

    def get_current_price(self):
        return self.exchange.get_current_price(self.symbol)
    
    def calculate_trade_cost(self, trade_amount: float, price: float):
        # Get the cost of a transaction
        return price * trade_amount * self.transaction_costs

    def record_trade(self, action: str, trade_amount: float, price: float, trade_date: datetime, cost: float):
        # Record the trade
        cash_value = price * trade_amount
        
        if action == TradeAction.BUY:
            self.cash -= (cash_value + cost) 
            self.tokens += trade_amount
        elif action == TradeAction.SELL:
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

    def get_valuation(self, price_at_valuation: float = None, valuation_point: datetime = None):
        if valuation_point is not None:
            if valuation_point < self.inception_date:
                raise ValueError("Valuation point is before the inception date of the portfolio.")
            if price_at_valuation is None:
                raise ValueError("A price must be provided when a specific valuation point is specified.")
            
            last_trade_before_valuation = self.get_last_trade_before(valuation_point)
            if last_trade_before_valuation:
                tokens_at_valuation = last_trade_before_valuation['current_tokens']
                cash_at_valuation = last_trade_before_valuation['current_cash']
            else:
                tokens_at_valuation = self.initial_tokens
                cash_at_valuation = self.initial_cash

            current_price = price_at_valuation
        else:
            tokens_at_valuation = self.tokens
            cash_at_valuation = self.cash
            current_price = price_at_valuation if price_at_valuation is not None else self.get_current_price()

        return cash_at_valuation + (tokens_at_valuation * current_price)

    def get_last_trade_before(self, date: datetime):
        for trade in reversed(self.trades):
            trade_date = self.strptime_utc(trade['date'], DATE_FORMAT)
            if trade_date < date:
                return trade
        return None
    
    def save_state(self, filename: str = None):
        file = filename if filename is not None else self.filename

        # Save the current state of the portfolio manager to disk
        state = {attr: (getattr(self, attr).strftime(DATE_FORMAT) if isinstance(getattr(self, attr), datetime) else getattr(self, attr))
                 for attr in self.__dict__ if not attr.startswith('_') and attr != 'exchange'}
        
        with open(file, 'w') as f:
            json.dump(state, f)

    def load_state(self, filename: str = None):
        file = filename if filename is not None else self.filename

        # Load the saved state of the portfolio manager from disk if available
        try:
            with open(file, 'r') as f:
                saved_state = json.load(f)
                for key, value in saved_state.items():
                    if key == 'inception_date':
                        setattr(self, key, self.strptime_utc(value, DATE_FORMAT))
                    else:
                        setattr(self, key, value)

        except FileNotFoundError:
            pass
        
    def __str__(self):
        return f"Cash: {self.cash}, Tokens: {self.tokens}, Trades: {self.trades}"

    @staticmethod
    def strptime_utc(date_str, date_format):
        return datetime.strptime(date_str, date_format).replace(tzinfo=timezone.utc)
