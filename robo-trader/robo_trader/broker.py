from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

class OrderType:
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP_LOSS = 'STOP_LOSS'
    TRAILING_STOP = 'TRAILING_STOP'
    TAKE_PROFIT = 'TAKE_PROFIT'

class OrderSide:
    BUY = 'BUY'
    SELL = 'SELL'

class OrderStatus:
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'
    PENDING = 'PENDING'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'

@dataclass
class Trade:
    id: str
    order_id: str
    symbol: str
    order_type: str
    order_side: str
    price: float
    quantity: float
    timestamp: datetime
    transaction_costs: float

@dataclass
class Order:
    symbol: str
    order_type: str
    order_side: str
    quantity: float
    trail: float
    limit: float
    stop: float
    id: str
    timestamp: datetime
    status: str = OrderStatus.PENDING
    trades: list[Trade] = None

    def __post_init__(self):
        if self.trades is None:
            self.trades = []    

class Broker(ABC):
    @abstractmethod
    def create_order(self, symbol: str, order_type: str, order_side: str, quantity: float = None, cash_amount: float = None, trail: float = None, limit: float = None, stop: float = None, take_profit: float = None) -> Order:
        pass

    @abstractmethod
    def edit_order(self, order_id, stop):
        pass

    @abstractmethod
    def cancel_order(self, order_id):
        pass

    @abstractmethod
    def fetch_order(self, order_id) -> Order:
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass