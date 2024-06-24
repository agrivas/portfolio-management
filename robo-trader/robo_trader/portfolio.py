from .broker import Broker, Order, OrderType, OrderSide, OrderStatus, Trade
from typing import Dict, List
from datetime import datetime
import json
import uuid

class Portfolio:
    def __init__(self, broker: Broker, initial_cash: float = None, load_from_file: str = None):
        self.broker = broker
        if load_from_file:
            self._load_state(load_from_file)
        else:
            self.cash = initial_cash
            self.asset_holdings: Dict[str, float] = {}
            self.orders: Dict[str, Order] = {}
            self.processed_trades = set()
            self.open_trail = {}
            self.valuation_history: List[Dict[str, float]] = []
            self.uuid = str(uuid.uuid4())

    def open_long(self, symbol: str, cash_percentage: float, trail_percentage: float = None) -> Order:
        if cash_percentage <= 0 or cash_percentage > 1:
            raise ValueError("Percentage must be between 0 and 1")

        print(f"Request to open long position on {symbol}")
        if self.is_long(symbol):
            print(f"    Already long on {symbol}")
            return None

        amount_to_invest = self.cash * cash_percentage    

        print(f"    Opening long position for {symbol} with for {cash_percentage*100}% of the cash (£{amount_to_invest}) and {trail_percentage*100}% trail")
        order = self.broker.create_order(symbol, OrderType.MARKET, OrderSide.BUY, cash_amount=amount_to_invest, trail=trail_percentage)
    
        self.orders[order.id] = order
        self.open_trail[symbol] = trail_percentage

        self._update_orders()

    def close_long(self, symbol: str):
        print(f"Request to close long position on {symbol}")
        if not self.is_long(symbol):
            print(f"    No long position on {symbol}")
            return None
        
        # Cancel any pending trailing stop order for the symbol
        pending_trailing_stop = next((order for order in self.orders.values() if 
                                      order.symbol == symbol and 
                                      order.order_side == OrderSide.SELL and 
                                      order.order_type == OrderType.TRAILING_STOP and 
                                      order.status == OrderStatus.PENDING), 
                                     None)
        if pending_trailing_stop:
            self.broker.cancel_order(pending_trailing_stop.id)
            del self.orders[pending_trailing_stop.id]
            print(f"    Cancelled pending trailing stop order for {symbol}")

        print(f"    Closing long position for {symbol}")            
        order = self.broker.create_order(symbol, OrderType.MARKET, OrderSide.SELL, self.asset_holdings[symbol])
        
        self.orders[order.id] = order
        self.open_trail[symbol] = None

        self._update_orders()

    def update(self, time: datetime, prices: Dict[str, float] = None):
        self._update_orders()

        # Update valuation history
        current_valuation = self.get_valuation(time, prices)
        self.valuation_history.append({"timestamp": time, "valuation": current_valuation})

        # Persist the state of the portfolio on disk
        self._persist_state()

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

    def is_long(self, symbol: str) -> bool:
        return symbol in self.asset_holdings and self.asset_holdings[symbol] > 0
    
    def _update_orders(self):
        for order_id, order in self.orders.items():
            updated_order = order

            if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                updated_order = self.broker.fetch_order(order_id)
                self.orders[order_id] = updated_order
            
            self._process_order(updated_order)

        # Check if we hold any asset and ensure there's an active trailing stop sell order
        for symbol, quantity in self.asset_holdings.items():
            if quantity > 0:
                if self.open_trail[symbol] is None:
                    continue

                active_sell_order = next((order for order in self.orders.values() if 
                                          order.symbol == symbol and 
                                          order.order_side == OrderSide.SELL and 
                                          order.order_type == OrderType.TRAILING_STOP and
                                          order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]), 
                                         None)
                
                if not active_sell_order:
                    # Create a new trailing stop sell order
                    new_order = self.broker.create_order(symbol, OrderType.TRAILING_STOP, OrderSide.SELL, quantity=quantity, trail=self.open_trail[symbol])
                    self.orders[new_order.id] = new_order
            else:
                self.open_trail[symbol] = None

    def _process_order(self, order):
        for trade in order.trades:
            if trade.id not in self.processed_trades:
                if order.order_side == OrderSide.BUY:
                    print(f"    Bought {trade.quantity} {trade.symbol} at {trade.price}")
                    self.cash -= (trade.price * trade.quantity + trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) + trade.quantity
                elif order.order_side == OrderSide.SELL:
                    print(f"    Sold {trade.quantity} {trade.symbol} at {trade.price}")
                    self.cash += (trade.price * trade.quantity - trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) - trade.quantity
                self.processed_trades.add(trade.id)

    def _persist_state(self):
        state = {
            "cash": self.cash,
            "asset_holdings": self.asset_holdings,
            "orders": {
                order_id: {
                    **order.__dict__,
                    "trades": [trade.__dict__ for trade in order.trades]
                } for order_id, order in self.orders.items()
            },
            "processed_trades": list(self.processed_trades),
            "open_trail": self.open_trail,
            "valuation_history": self.valuation_history,
            "uuid": self.uuid
        }
        filename = f"portfolio_{self.uuid}.json"
        with open(filename, 'w') as f:
            json.dump(state, f, default=str)  # Use default=str to handle datetime objects

    def _load_state(self, filename: str):
        with open(filename, 'r') as f:
            state = json.load(f)
        
        self.cash = state["cash"]
        self.asset_holdings = state["asset_holdings"]
        self.orders = {
            order_id: Order(
                **{k: v for k, v in order_dict.items() if k != 'trades'},
                trades=[Trade(**trade_dict) for trade_dict in order_dict['trades']]
            ) for order_id, order_dict in state["orders"].items()
        }
        self.processed_trades = set(state["processed_trades"])
        self.open_trail = state["open_trail"]
        self.valuation_history = state["valuation_history"]
        self.uuid = state["uuid"]
