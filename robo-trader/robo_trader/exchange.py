from datetime import datetime
from abc import ABC, abstractmethod
from .types import TradeAction, Trade

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
    def __init__(self, price_map: dict):
        """
        Initialize the DummyExchange with a predefined set of prices for symbols.
        
        :param price_map: A dictionary mapping symbols to their mocked prices.
        """
        self.price_map = price_map
        self.trades = []

    def execute_trade(self, symbol: str, trade_action: TradeAction, trade_amount: float) -> Trade:
        """
        Simulate the execution of a trade and record it.
        
        :param symbol: The trading symbol.
        :param trade_action: The action of the trade, either 'BUY' or 'SELL'.
        :param trade_amount: The amount to trade.
        :return: A Trade object representing the executed trade.
        """
        price = self.get_current_price(symbol)
        cost = trade_amount * price * 0.01  # Assume a 1% transaction cost for simplicity
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
