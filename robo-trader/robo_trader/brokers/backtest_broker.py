import uuid
from typing import Dict
from robo_trader.broker import Broker, Order, OrderType, OrderSide, OrderStatus, Trade
from datetime import datetime, timedelta

class BacktestBroker(Broker):
    def __init__(self, transaction_cost: float = 0, trailing_stop_penalty_relief: float = 0.75):
        self.orders: Dict[str, Order] = {}
        self.current_prices: Dict[str, float] = {}
        self.current_timestamp: datetime = None
        self.transaction_cost = transaction_cost
        self.trailing_stop_penalty_relief = trailing_stop_penalty_relief

    def create_order(self, symbol: str, order_type: str, order_side: str, quantity: float = None, cash_amount: float = None, trail: float = None, limit: float = None, stop: float = None, take_profit: float = None) -> Order:
        if (quantity is None and cash_amount is None) or (quantity is not None and cash_amount is not None):
            raise ValueError("Exactly one of quantity or cash_amount must be provided")
        
        if quantity is not None and quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if cash_amount is not None and cash_amount <= 0:
            raise ValueError("Cash amount must be positive")

        if trail is not None and take_profit is not None:
            raise ValueError("Only one of trail or take_profit can be set")

        current_price = self.get_price(symbol)
        if current_price <= 0:
            raise ValueError(f"Invalid price for {symbol}: {current_price}")

        # Calculate the maximum quantity that can be bought with the given cash amount
        if not quantity:
            transaction_cost = cash_amount * self.transaction_cost
            available_cash = cash_amount - transaction_cost
            quantity = available_cash / current_price

        stop_amount = None
        if order_type == OrderType.TRAILING_STOP:
            if order_side == OrderSide.BUY:
                stop_amount = current_price * (1 + trail)
            elif order_side == OrderSide.SELL:
                stop_amount = current_price * (1 - trail)
        elif order_type == OrderType.TAKE_PROFIT:
            if order_side == OrderSide.BUY:
                stop_amount = current_price * (1 - take_profit)
            elif order_side == OrderSide.SELL:
                stop_amount = current_price * (1 + take_profit)
        elif order_type == OrderType.STOP_LOSS:
            if order_side == OrderSide.BUY:
                stop_amount = current_price * (1 + stop)
            elif order_side == OrderSide.SELL:
                stop_amount = current_price * (1 - stop)

        trail_amount = trail * current_price if trail is not None else None

        limit_amount = None
        if order_type == OrderType.LIMIT:
            if order_side == OrderSide.BUY:
                limit_amount = current_price * (1 - limit)
            elif order_side == OrderSide.SELL:
                limit_amount = current_price * (1 + limit)

        order_id = str(uuid.uuid4())
        timestamp = self.current_timestamp

        print(f"    Creating {order_type} {order_side} order for {symbol} at {current_price} with quantity {quantity}, trail {trail}, limit {limit}, stop {stop}, take_profit {take_profit}")
        order = Order(id=order_id, symbol=symbol, order_type=order_type, order_side=order_side, status=OrderStatus.PENDING, quantity=quantity, trail=trail_amount, limit=limit_amount, stop=stop_amount, timestamp=timestamp)

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

    def update(self, timestamp: datetime, prices: Dict[str, float]):
        self.current_timestamp = timestamp
        self.current_prices = prices

        for order_id, order in self.orders.items():
            if order.status == OrderStatus.PENDING:
                current_price = self.current_prices.get(order.symbol)
                if current_price is not None:
                    if order.order_type == OrderType.STOP_LOSS:
                        if (order.order_side == OrderSide.BUY and current_price >= order.stop) or \
                           (order.order_side == OrderSide.SELL and current_price <= order.stop):
                            self._execute_order(order)
                    elif order.order_type == OrderType.TRAILING_STOP:
                        # Simulating how trailing stop would have been triggered
                        price_difference = current_price - order.stop
                        trade_price = current_price - (price_difference * self.trailing_stop_penalty_relief)
                        trade_timestamp = self.current_timestamp - timedelta(seconds=1)

                        if order.order_side == OrderSide.BUY:                            
                            if price_difference >= 0:
                                self._execute_order(order, trade_timestamp, trade_price)
                            else:   
                                new_stop = current_price + order.trail
                                if new_stop < order.stop:
                                    order.stop = new_stop
                                    print(f"    Updated trailing stop to {order.stop}")
                        elif order.order_side == OrderSide.SELL:
                            if price_difference <= 0:
                                self._execute_order(order, trade_timestamp, trade_price)
                            else:
                                new_stop = current_price - order.trail
                                if new_stop > order.stop:
                                    order.stop = new_stop
                                    print(f"    Updated trailing stop to {order.stop}")
                    elif order.order_type == OrderType.TAKE_PROFIT:
                        if order.order_side == OrderSide.BUY:
                            if current_price <= order.stop:
                                self._execute_order(order)
                        elif order.order_side == OrderSide.SELL:
                            if current_price >= order.stop:
                                self._execute_order(order)

    def _execute_order(self, order: Order, timestamp: datetime = None, price: float = None):
        if timestamp is None:
            timestamp = self.current_timestamp
        if price is None:
            price = self.current_prices.get(order.symbol, 0)

        asset_cost = price * order.quantity
        transaction_cost = asset_cost * self.transaction_cost
        total_cost = asset_cost + transaction_cost
        
        print(f"    Executing {order.order_type} {order.order_side} order for {order.symbol} at {price} with quantity {order.quantity}, total cost £{total_cost} and transaction cost £{transaction_cost}")

        trade = Trade(
            id=str(uuid.uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            order_type=order.order_type,
            order_side=order.order_side,
            price=price,
            quantity=order.quantity,
            timestamp=timestamp,
            transaction_costs=transaction_cost
        )
        order.trades.append(trade)
        order.status = OrderStatus.FILLED

        return order


