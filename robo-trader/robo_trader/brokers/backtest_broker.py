import uuid
from typing import Dict
from ..broker import Broker, Order, OrderType, OrderSide, OrderStatus, Trade
from datetime import datetime

class BacktestBroker(Broker):
    def __init__(self, transaction_cost_percentage: float = 0):
        self.orders: Dict[str, Order] = {}
        self.current_prices: Dict[str, float] = {}
        self.current_timestamp: datetime = None
        self.transaction_cost_percentage = transaction_cost_percentage

    def create_order(self, symbol: str, order_type: str, order_side: str, cash_amount: float, trail: float = None, limit: float = None, stop: float = None) -> Order:
        current_price = self.get_price(symbol)
        if current_price <= 0:
            raise ValueError(f"Invalid price for {symbol}: {current_price}")

        # Calculate the maximum quantity that can be bought with the given cash amount
        transaction_cost = cash_amount * self.transaction_cost_percentage
        available_cash = cash_amount - transaction_cost
        quantity = available_cash / current_price

        # Round down to ensure we don't exceed the cash amount
        quantity = int(quantity)

        order_id = str(uuid.uuid4())
        order = Order(id=order_id, symbol=symbol, order_type=order_type, order_side=order_side, quantity=quantity, trail=trail, limit=limit, stop=stop)
        self.orders[order_id] = order
        self._execute_order(order)  # Immediately execute the order
        return order

    def edit_order(self, order_id: str, stop: float):
        if order_id in self.orders:
            self.orders[order_id].stop = stop

    def cancel_order(self, order_id: str):
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELLED

    def fetch_order(self, order_id: str) -> Order:
        return self.orders.get(order_id)

    def get_price(self, symbol: str) -> float:
        return self.current_prices.get(symbol, 0)

    def update(self):
        for order_id, order in self.orders.items():
            if order.status == OrderStatus.PENDING:
                current_price = self.current_prices.get(order.symbol)
                if current_price is not None:
                    if order.order_type == OrderType.STOP:
                        if (order.order_side == OrderSide.BUY and current_price >= order.stop) or \
                           (order.order_side == OrderSide.SELL and current_price <= order.stop):
                            self._execute_order(order)
                    elif order.order_type == OrderType.TRAILING_STOP:
                        if order.order_side == OrderSide.BUY:
                            new_stop = current_price * (1 - order.trail / 100)
                            if new_stop > order.stop:
                                order.stop = new_stop
                            elif current_price >= order.stop:
                                self._execute_order(order)
                        elif order.order_side == OrderSide.SELL:
                            new_stop = current_price * (1 + order.trail / 100)
                            if new_stop < order.stop:
                                order.stop = new_stop
                            elif current_price <= order.stop:
                                self._execute_order(order)

    def set_price(self, symbol: str, price: float):
        self.current_prices[symbol] = price

    def set_timestamp(self, timestamp: datetime):
        self.current_timestamp = timestamp

    def _execute_order(self, order: Order):
        current_price = self.current_prices.get(order.symbol, 0)
        transaction_costs = current_price * order.quantity * self.transaction_cost_percentage
        trade = Trade(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            order_type=order.order_type,
            order_side=order.order_side,
            price=current_price,
            quantity=order.quantity,
            timestamp=self.current_timestamp,
            transaction_costs=transaction_costs
        )
        order.trades.append(trade)
        order.status = OrderStatus.FILLED

