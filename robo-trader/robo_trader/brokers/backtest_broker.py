import uuid
from typing import Dict
from robo_trader.broker import Broker, Order, OrderType, OrderSide, OrderStatus, Trade
from datetime import datetime

class BacktestBroker(Broker):
    def __init__(self, transaction_cost: float = 0):
        self.orders: Dict[str, Order] = {}
        self.current_prices: Dict[str, float] = {}
        self.current_timestamp: datetime = None
        self.transaction_cost = transaction_cost

    def create_order(self, symbol: str, order_type: str, order_side: str, quantity: float = None, cash_amount: float = None, trail: float = None, limit: float = None, stop: float = None) -> Order:
        if (quantity is None and cash_amount is None) or (quantity is not None and cash_amount is not None):
            raise ValueError("Exactly one of quantity or cash_amount must be provided")
        
        if quantity is not None and quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if cash_amount is not None and cash_amount <= 0:
            raise ValueError("Cash amount must be positive")

        current_price = self.get_price(symbol)
        if current_price <= 0:
            raise ValueError(f"Invalid price for {symbol}: {current_price}")

        # Calculate the maximum quantity that can be bought with the given cash amount
        if not quantity:
            transaction_cost = cash_amount * self.transaction_cost
            available_cash = cash_amount - transaction_cost
            quantity = available_cash / current_price

        if order_type == OrderType.TRAILING_STOP:
            if order_side == OrderSide.BUY:
                stop = current_price * (1 - trail)
            elif order_side == OrderSide.SELL:
                stop = current_price * (1 + trail)

        order_id = str(uuid.uuid4())

        print(f"    Creating {order_type} {order_side} order for {symbol} with quantity {quantity} at {current_price}")
        order = Order(id=order_id, symbol=symbol, order_type=order_type, order_side=order_side, status=OrderStatus.PENDING, quantity=quantity, trail=trail, limit=limit, stop=stop)

        if order_type == OrderType.MARKET or order_type == OrderType.LIMIT:
            order = self._execute_order(order)

        self.orders[order_id] = order

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
                            if current_price >= order.stop:
                                self._execute_order(order)
                            else:   
                                new_stop = current_price * (1 + order.trail)
                                if new_stop < order.stop:
                                    order.stop = new_stop
                                    print(f"    Updated trailing stop to {order.stop}")
                        elif order.order_side == OrderSide.SELL:
                            if current_price <= order.stop:
                                self._execute_order(order)
                            else:
                                new_stop = current_price * (1 - order.trail)
                                if new_stop > order.stop:
                                    order.stop = new_stop
                                    print(f"    Updated trailing stop to {order.stop}")

    def set_price(self, symbol: str, price: float):
        self.current_prices[symbol] = price

    def set_timestamp(self, timestamp: datetime):
        self.current_timestamp = timestamp

    def _execute_order(self, order: Order):
        current_price = self.current_prices.get(order.symbol, 0)
        transaction_costs = current_price * order.quantity * self.transaction_cost
        
        print(f"    Executing {order.order_type} {order.order_side} order for {order.symbol} with quantity {order.quantity} at {current_price}")

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

        return order

