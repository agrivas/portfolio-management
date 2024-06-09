from datetime import datetime
from abc import ABC, abstractmethod
from .types import TradeAction
from dataclasses import dataclass

@dataclass
class Trade:
    action: TradeAction
    success: bool
    trade_amount: float
    price: float
    date: datetime
    cost: float

class Exchange(ABC):
    @abstractmethod
    def execute_trade(self, symbol: str, trade_action: TradeAction, trade_amount: float) -> Trade:
        """
        Execute a trade on the exchange.
        
        :param trade_action: The action of the trade, either 'BUY' or 'SELL'
        :param amount: The amount to trade
        :param price: The price at which to execute the trade
        """
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price of the asset from the exchange.
        
        :return: The current price as a float
        """
        pass

class DummyExchange(Exchange):
    def __init__(self, price_map: dict, transaction_costs: float):
        """
        Initialize the DummyExchange with a predefined set of prices for symbols.
        
        :param price_map: A dictionary mapping symbols to their mocked prices.
        """
        self.price_map = price_map
        self.trades = []
        self.current_date = datetime.now()
        self.transaction_costs = transaction_costs

    def execute_trade(self, symbol: str, trade_action: TradeAction, trade_amount: float) -> Trade:
        """
        Simulate the execution of a trade and record it.
        
        :param symbol: The trading symbol.
        :param trade_action: The action of the trade, either 'BUY' or 'SELL'.
        :param trade_amount: The amount to trade.
        :return: A Trade object representing the executed trade.
        """
        price = self.get_current_price(symbol)
        cost = trade_amount * price * self.transaction_costs
        trade = Trade(action=trade_action, success=True, trade_amount=trade_amount, price=price, date=datetime.now(), cost=cost)
        self.trades.append(trade)
        return trade

    def get_current_price(self, symbol: str) -> float:
        """
        Get the mocked current price of the asset from the exchange.
        
        :param symbol: The trading symbol.
        :return: The mocked current price as a float.
        """
        return self.price_map.get(symbol, 0.0)

    def set_current_price(self, symbol: str, price: float):
        """
        Set the current price of the asset from the exchange.
        
        :param symbol: The trading symbol.
        :param price: The current price as a float.
        """
        self.price_map[symbol] = price

    def get_current_date(self) -> datetime:
        """
        Get the current date and time.
        
        :return: The current datetime object.
        """
        return self.current_date

    def set_current_date(self, new_date: datetime):
        """
        Set the current date and time. This is mainly for testing purposes to simulate different times.
        
        :param new_date: The new datetime to set as the current datetime.
        """
        self.current_date = new_date
