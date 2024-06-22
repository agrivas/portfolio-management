from .broker import Broker, Order, OrderType, OrderSide, OrderStatus
from typing import Dict
from datetime import datetime

class Portfolio:
    def __init__(self, broker: Broker, initial_cash: float):
        self.broker = broker
        self.cash = initial_cash
        self.asset_holdings: Dict[str, float] = {}
        self.orders: Dict[str, Order] = {}
        self.processed_trades = set()
        self.open_trail = {}

    def open_long(self, symbol: str, percentage: float, trail: float) -> Order:
        if percentage <= 0 or percentage > 1:
            raise ValueError("Percentage must be between 0 and 1")
        
        amount_to_invest = self.cash * percentage
        
        order = self.broker.create_order(symbol, OrderType.TRAILING_STOP, OrderSide.BUY, amount_to_invest, trail=trail)
        self.orders[order.id] = order
        self.open_trail[symbol] = trail
        return order

    def close_long(self, symbol: str):
        if symbol in self.asset_holdings and self.asset_holdings[symbol] > 0:
            order = self.broker.create_order(symbol, OrderType.MARKET, OrderSide.SELL, self.asset_holdings[symbol])
            self.orders[order.id] = order
            self.open_trail[symbol] = None

    def update(self):
        for order_id, order in self.orders.items():
            if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                updated_order = self.broker.fetch_order(order_id)
                self.orders[order_id] = updated_order
                self._process_order(updated_order)

        # Check if we hold any asset and ensure there's an active trailing stop sell order
        for symbol, quantity in self.asset_holdings.items():
            if quantity > 0:
                active_sell_order = next((order for order in self.orders.values() if 
                                          order.symbol == symbol and 
                                          order.order_side == OrderSide.SELL and 
                                          order.order_type == OrderType.TRAILING_STOP and
                                          order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]), 
                                         None)
                
                if not active_sell_order:
                    # Create a new trailing stop sell order
                    new_order = self.broker.create_order(symbol, OrderType.TRAILING_STOP, OrderSide.SELL, quantity, trail=self.open_trail[symbol])
                    self.orders[new_order.id] = new_order
            else:
                self.open_trail[symbol] = None   

    def get_valuation(self, time: datetime = None, prices: Dict[str, float] = None) -> float:
        if (time is None) != (prices is None):
            raise ValueError("Both time and prices must be provided together, or neither should be provided.")

        total_value = self.cash

        for symbol, quantity in self.asset_holdings.items():
            if time is not None and prices is not None:
                if symbol not in prices:
                    raise ValueError(f"Price for symbol {symbol} not provided in prices dictionary.")
                price = prices[symbol]
            else:
                price = self.broker.get_price(symbol)

            total_value += quantity * price

        return total_value
    
    def _process_order(self, order):
        for trade in order.trades:
            if trade.id not in self.processed_trades:
                if order.order_side == OrderSide.BUY:
                    self.cash -= (trade.price * trade.quantity + trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) + trade.quantity
                elif order.order_side == OrderSide.SELL:
                    self.cash += (trade.price * trade.quantity - trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) - trade.quantity
                self.processed_trades.add(trade.id)
