from .broker import Broker, Order, OrderType, OrderSide, OrderStatus, Trade
from typing import Dict, List
from datetime import datetime
import json
import uuid
from enum import Enum
import pandas as pd
import matplotlib.pyplot as plt

class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"

    def __str__(self):
        return self.value

class Position:
    def __init__(self, symbol: str, side: PositionSide, amount_invested: float, trail_percentage: float = None, take_profit_percentage: float = None, stop_percentage: float = None):
        self.symbol = symbol
        self.side = side
        self.amount_invested = amount_invested
        self.trail_percentage = trail_percentage
        self.take_profit_percentage = take_profit_percentage
        self.stop_percentage = stop_percentage
        self.is_open = True
        self.open_price = None
        self.close_price = None
        self.quantity = None
        self.order_ids = []

    def set_quantity(self, quantity: float):
        self.quantity = quantity
        self.open_price = self.amount_invested / quantity if quantity else None

    def close(self, close_price: float):
        self.is_open = False
        self.close_price = close_price

class Portfolio:
    def __init__(self, broker: Broker, initial_cash: float = None, autosave: bool = True):
        self.broker = broker
        self.autosave = autosave        
        self.cash = initial_cash
        self.asset_holdings: Dict[str, float] = {}
        self.orders: Dict[str, Order] = {}
        self.processed_trades = set()
        self.positions: List[Position] = []
        self.valuation_history: List[Dict[str, float]] = []
        self.uuid = str(uuid.uuid4())

    # Overrides
    def __str__(self):
        return f"Portfolio(cash={self.cash}, assets={self.asset_holdings})"

    # Public methods
    def open_long(self, symbol: str, cash_percentage: float, trail_percentage: float = None, take_profit_percentage: float = None, stop_percentage: float = None) -> Order:
        if cash_percentage <= 0 or cash_percentage > 1:
            raise ValueError("Percentage must be between 0 and 1")

        if trail_percentage is not None and stop_percentage is not None:
            raise ValueError("Trail percentage cannot be used with stop loss")

        if stop_percentage is not None and take_profit_percentage is None:
            raise ValueError("Stop percentage always requires a take profit percentage")

        print(f"Request to open long position on {symbol}")
        if self.is_long(symbol):
            print(f"    Already long on {symbol}")
            return None

        amount_to_invest = self.cash * cash_percentage    

        print(f"    Opening long position for {symbol} with for {cash_percentage*100}% of the cash (£{amount_to_invest})")
        order = self.broker.create_order(symbol, OrderType.MARKET, OrderSide.BUY, cash_amount=amount_to_invest)
    
        self.orders[order.id] = order
        
        # Create a new position
        position = Position(symbol, PositionSide.LONG, amount_to_invest, trail_percentage, take_profit_percentage, stop_percentage)
        position.order_ids.append(order.id)
        self.positions.append(position)

        self._update_orders()

    def close_long(self, symbol: str):
        print(f"Request to close long position on {symbol}")
        if not self.is_long(symbol):
            print(f"    No long position on {symbol}")
            return None
        
        # Find the open position for this symbol
        position = next((pos for pos in self.positions if pos.symbol == symbol and pos.is_open and pos.side == PositionSide.LONG), None)
        if not position:
            print(f"    No open long position found for {symbol}")
            return None

        # Cancel any pending trailing stop, take profit, or stop loss order for the symbol
        pending_sell_orders = [order for order in self.orders.values() if 
                               order.symbol == symbol and 
                               order.order_side == OrderSide.SELL and 
                               (order.order_type in [OrderType.TRAILING_STOP, OrderType.TAKE_PROFIT, OrderType.STOP_LOSS]) and 
                               order.status == OrderStatus.PENDING]
        for pending_sell_order in pending_sell_orders:
            self.broker.cancel_order(pending_sell_order.id)
            del self.orders[pending_sell_order.id]
            print(f"    Cancelled pending sell order for {symbol}")

        print(f"    Closing long position for {symbol}")            
        order = self.broker.create_order(symbol, OrderType.MARKET, OrderSide.SELL, self.asset_holdings[symbol])
        
        self.orders[order.id] = order
        position.order_ids.append(order.id)

        self._update_orders()

    def update(self, time: datetime, prices: Dict[str, float] = None):
        self._update_orders()

        # Update valuation history on every update
        current_valuation = self.get_valuation(time, prices)
        self.valuation_history.append({
            "timestamp": time,
            "valuation": current_valuation,
            "prices": prices,
            "asset_holdings": self.asset_holdings.copy()
        })

        # Autosave on every update if enabled
        if self.autosave:
            self.save()

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
    
    def save(self):
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
            "positions": [{**pos.__dict__, "side": str(pos.side)} for pos in self.positions],
            "valuation_history": self.valuation_history,
            "uuid": self.uuid,
            "autosave": self.autosave
        }
        filename = f"portfolio_{self.uuid}.json"
        with open(filename, 'w') as f:
            json.dump(state, f, indent=4, default=str)  # Use indent=4 for human-readable formatting and default=str to handle datetime objects

    @staticmethod
    def from_file(broker: Broker, filename: str) -> 'Portfolio':
        with open(filename, 'r') as f:
            state = json.load(f)
        
        portfolio = Portfolio(broker)
        portfolio.cash = state["cash"]
        portfolio.asset_holdings = state["asset_holdings"]
        portfolio.orders = {
            order_id: Order(
                **{k: v for k, v in order_dict.items() if k != 'trades'},
                trades=[Trade(**trade_dict) for trade_dict in order_dict['trades']]
            ) for order_id, order_dict in state["orders"].items()
        }
        portfolio.processed_trades = set(state["processed_trades"])
        portfolio.positions = [Position(**{**pos_dict, "side": PositionSide(pos_dict["side"])}) for pos_dict in state["positions"]]
        portfolio.valuation_history = state["valuation_history"]
        portfolio.uuid = state["uuid"]
        portfolio.autosave = state.get("autosave", True)
        return portfolio

    def calculate_performance(self):
        initial_portfolio_valuation = self.valuation_history[0]['valuation']
        final_portfolio_valuation = self.valuation_history[-1]['valuation']
        portfolio_return = (final_portfolio_valuation - initial_portfolio_valuation) / initial_portfolio_valuation

        # Calculate win rate
        closed_positions = [pos for pos in self.positions if not pos.is_open]
        winning_trades = sum(1 for pos in closed_positions if pos.close_price > pos.open_price)
        total_trades = len(closed_positions)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Create a timeseries DataFrame
        df = pd.DataFrame(self.valuation_history)
        df['asset_price'] = [v['prices'][list(v['prices'].keys())[0]] for v in self.valuation_history]
        df['portfolio_value'] = df['valuation']
        df['open_long'] = False
        df['close_long'] = False

        # Populate open_long and close_long columns using trades
        for order in self.orders.values():
            for trade in order.trades:
                trade_index = df[df['timestamp'] >= trade.timestamp].index[0]
                if order.order_side == OrderSide.BUY:
                    df.loc[trade_index, 'open_long'] = True
                elif order.order_side == OrderSide.SELL:
                    df.loc[trade_index, 'close_long'] = True

        # Calculate asset return
        initial_asset_price = df['asset_price'].iloc[0]
        final_asset_price = df['asset_price'].iloc[-1]
        asset_return = (final_asset_price - initial_asset_price) / initial_asset_price

        # Calculate buy and hold return
        initial_buy_and_hold_quantity = initial_portfolio_valuation / initial_asset_price
        df['buy_and_hold_value'] = initial_buy_and_hold_quantity * df['asset_price']

        # Calculate portfolio_return and buy_and_hold_return series
        df['portfolio_return'] = (df['portfolio_value'] - initial_portfolio_valuation) / initial_portfolio_valuation
        df['buy_and_hold_return'] = (df['buy_and_hold_value'] - initial_portfolio_valuation) / initial_portfolio_valuation

        # Calculate max drawdown for portfolio
        df['portfolio_cummax'] = df['portfolio_value'].cummax()
        df['portfolio_drawdown'] = (df['portfolio_value'] - df['portfolio_cummax']) / df['portfolio_cummax']
        portfolio_max_drawdown = df['portfolio_drawdown'].min()

        # Calculate max drawdown for asset
        df['asset_cummax'] = df['asset_price'].cummax()
        df['asset_drawdown'] = (df['asset_price'] - df['asset_cummax']) / df['asset_cummax']
        asset_max_drawdown = df['asset_drawdown'].min()

        performance_stats = {
            'initial_value': initial_portfolio_valuation,
            'final_value': final_portfolio_valuation,
            'win_rate': win_rate,
            'portfolio_return': portfolio_return,
            'asset_return': asset_return,
            'portfolio_max_drawdown': portfolio_max_drawdown,
            'asset_max_drawdown': asset_max_drawdown,
            'performance': df
        }

        return performance_stats

    def plot_performance(self):
        results = self.calculate_performance()

        # Print performance metrics as text
        print(f"Win Rate: {results['win_rate']:.2f}")
        print(f"Initial Value: {results['initial_value']:.2f}")
        print(f"Final Value: {results['final_value']:.2f}")
        print(f"Portfolio Return: {results['portfolio_return']:.4f}")
        print(f"Asset Return: {results['asset_return']:.4f}")

        # Convert the index to datetime if it's not already
        results['performance'].index = pd.to_datetime(results['performance'].index)

        # Create the plot with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(38, 36), gridspec_kw={'height_ratios': [1, 1, 1]})

        # Plot the price on the first subplot
        ax1.plot(results['performance'].index, results['performance']['asset_price'], color='blue', label='Price')

        # Plot green arrows for open_long
        open_long = results['performance'][results['performance']['open_long']]
        ax1.scatter(open_long.index, open_long['asset_price'], color='green', marker='^', s=300, label='Open Long')

        # Plot red arrows for close_long
        close_long = results['performance'][results['performance']['close_long']]
        ax1.scatter(close_long.index, close_long['asset_price'], color='red', marker='v', s=300, label='Close Long')

        # Customize the first subplot
        ax1.set_title('Trading Signals', fontsize=24)
        ax1.set_ylabel('Price', fontsize=24)
        ax1.legend(fontsize=24)
        ax1.xaxis.set_major_formatter(plt.NullFormatter())

        # Plot the portfolio value on the second subplot
        ax2.plot(results['performance'].index, results['performance']['portfolio_value'], color='purple', label='Portfolio Value')

        # Customize the second subplot
        ax2.set_title('Portfolio Value', fontsize=24)
        ax2.set_ylabel('Value', fontsize=24)
        ax2.legend(fontsize=24)
        ax2.xaxis.set_major_formatter(plt.NullFormatter())

        # Plot portfolio return and buy-and-hold return on the third subplot
        ax3.plot(results['performance'].index, results['performance']['portfolio_return'], color='green', label='Portfolio Return')
        ax3.plot(results['performance'].index, results['performance']['buy_and_hold_return'], color='orange', label='Buy and Hold Return')

        # Customize the third subplot
        ax3.set_title('Portfolio Return vs Buy and Hold Return', fontsize=24)
        ax3.set_ylabel('Return', fontsize=24)
        ax3.legend(fontsize=24)
        ax3.xaxis.set_major_formatter(plt.NullFormatter())

        # Adjust the layout and show the plot
        plt.tight_layout()
        plt.show()

        return results

    # Private helper methods
    def _update_orders(self):
        for order_id, order in self.orders.items():
            updated_order = order

            if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                updated_order = self.broker.fetch_order(order_id)
                self.orders[order_id] = updated_order
            
            self._process_order(updated_order)

        # Check if we hold any asset and ensure there's an active trailing stop, take profit, or stop loss sell order
        for position in self.positions:
            if position.is_open and position.side == PositionSide.LONG and position.quantity is not None:
                current_price = self.broker.get_price(position.symbol)
                active_sell_orders = [order for order in self.orders.values() if 
                                      order.symbol == position.symbol and 
                                      order.order_side == OrderSide.SELL and 
                                      order.order_type in [OrderType.TRAILING_STOP, OrderType.TAKE_PROFIT, OrderType.STOP_LOSS] and
                                      order.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]]
                
                if not active_sell_orders:
                    if position.trail_percentage is not None:
                        new_order = self.broker.create_order(position.symbol, OrderType.TRAILING_STOP, OrderSide.SELL, quantity=position.quantity, trail=position.trail_percentage)
                    elif position.take_profit_percentage is not None and position.stop_percentage is not None:
                        take_profit_order = self.broker.create_order(position.symbol, OrderType.TAKE_PROFIT, OrderSide.SELL, quantity=position.quantity, take_profit=position.take_profit_percentage)
                        stop_loss_order = self.broker.create_order(position.symbol, OrderType.STOP_LOSS, OrderSide.SELL, quantity=position.quantity, stop=position.stop_percentage)
                        self.orders[take_profit_order.id] = take_profit_order
                        self.orders[stop_loss_order.id] = stop_loss_order
                        position.order_ids.extend([take_profit_order.id, stop_loss_order.id])
                    else:
                        continue  # No trailing stop, take profit, or stop loss specified
                else:
                    # If we have a trailing stop and the price has increased, update the trailing stop
                    trailing_stop_order = next((order for order in active_sell_orders if order.order_type == OrderType.TRAILING_STOP), None)
                    if trailing_stop_order and current_price > position.open_price:
                        # Calculate the current profit percentage
                        profit_percentage = (current_price - position.open_price) / position.open_price
                        
                        # Reduce the trail percentage based on the profit
                        if profit_percentage > 0:
                            take_profit_coverage = profit_percentage / position.take_profit_percentage
                            new_trail_percentage = max(position.trail_percentage * (1 - min(take_profit_coverage, 1)), 0.001)  # Minimum 0.1% trail
                        
                            # Calculate the new stop price that locks in most of the current profit
                            new_stop_price = current_price * (1 - new_trail_percentage)
                            
                            if new_stop_price > trailing_stop_order.stop:
                                # Cancel the current trailing stop order
                                self.broker.cancel_order(trailing_stop_order.id)
                                # Create a new trailing stop order with the updated trail percentage
                                new_order = self.broker.create_order(position.symbol, OrderType.TRAILING_STOP, OrderSide.SELL, quantity=position.quantity, trail=new_trail_percentage)
                                print(f"Updated trailing stop for {position.symbol} to {new_stop_price:.2f} (trail: {new_trail_percentage:.2%})")
                
                if 'new_order' in locals():
                    self.orders[new_order.id] = new_order
                    position.order_ids.append(new_order.id)

    def _process_order(self, order):
        for trade in order.trades:
            if trade.id not in self.processed_trades:
                if order.order_side == OrderSide.BUY:
                    print(f"\033[92m        Bought {trade.quantity} {trade.symbol} at {trade.price} on {trade.timestamp.strftime('%d/%m/%Y %H:%M')}\033[0m")
                    self.cash -= (trade.price * trade.quantity + trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) + trade.quantity
                    
                    # Update the position with the actual quantity
                    position = next((pos for pos in self.positions if pos.symbol == trade.symbol and pos.is_open), None)
                    if position:
                        position.set_quantity(trade.quantity)
                elif order.order_side == OrderSide.SELL:
                    print(f"\033[91m        Sold {trade.quantity} {trade.symbol} at {trade.price} on {trade.timestamp.strftime('%d/%m/%Y %H:%M')}\033[0m")
                    self.cash += (trade.price * trade.quantity - trade.transaction_costs)
                    self.asset_holdings[trade.symbol] = self.asset_holdings.get(trade.symbol, 0) - trade.quantity
                    
                    # Close the position if it's a sell order
                    position = next((pos for pos in self.positions if pos.symbol == trade.symbol and pos.is_open), None)
                    if position:
                        position.close(trade.price)
                        
                        # Cancel the other order of the take profit / stop loss pair
                        if order.order_type in [OrderType.TAKE_PROFIT, OrderType.STOP_LOSS]:
                            other_order_type = OrderType.STOP_LOSS if order.order_type == OrderType.TAKE_PROFIT else OrderType.TAKE_PROFIT
                            other_order = next((o for o in self.orders.values() if 
                                                o.symbol == trade.symbol and 
                                                o.order_type == other_order_type and 
                                                o.status == OrderStatus.PENDING), None)
                            if other_order:
                                self.broker.cancel_order(other_order.id)
                                print(f"\033[93m        Cancelled {other_order_type} order for {trade.symbol}\033[0m")
                
                self.processed_trades.add(trade.id)
