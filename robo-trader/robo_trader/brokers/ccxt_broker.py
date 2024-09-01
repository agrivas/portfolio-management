import ccxt
from typing import Dict
from datetime import datetime
from robo_trader.broker import Broker, Order, OrderType, OrderStatus, Trade

class CCXTBroker(Broker):
    def __init__(self, exchange_id: str, api_key: str, secret: str):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })

    def create_order(self, symbol: str, order_type: str, order_side: str, quantity: float = None, cash_amount: float = None, trail: float = None, limit: float = None, stop: float = None, take_profit: float = None) -> Order:
        ccxt_order_type = self._convert_order_type(order_type)
        ccxt_order_side = order_side.lower()

        params = {}
        if trail:
            params['trailingAmount'] = trail
        if limit:
            params['price'] = limit
        if stop:
            params['stopPrice'] = stop
        if take_profit:
            params['takeProfitPrice'] = take_profit

        try:
            if quantity is not None:
                ccxt_order = self.exchange.create_order(symbol, ccxt_order_type, ccxt_order_side, quantity, None, params)
            elif cash_amount is not None:
                ccxt_order = self.exchange.create_market_buy_order(symbol, cash_amount) if order_side.lower() == 'buy' else self.exchange.create_market_sell_order(symbol, cash_amount)
            else:
                raise ValueError("Either quantity or cash_amount must be provided")
            
            return self._convert_to_order(ccxt_order)
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def edit_order(self, order_id, stop):
        try:
            ccxt_order = self.exchange.edit_order(order_id, None, None, None, None, {'stopPrice': stop})
            return self._convert_to_order(ccxt_order)
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def cancel_order(self, order_id):
        try:
            self.exchange.cancel_order(order_id)
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def fetch_order(self, order_id) -> Order:
        try:
            ccxt_order = self.exchange.fetch_order(order_id)
            return self._convert_to_order(ccxt_order)
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def get_price(self, symbol: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def _convert_order_type(self, order_type: str) -> str:
        order_type_map = {
            OrderType.MARKET: 'market',
            OrderType.LIMIT: 'limit',
            OrderType.STOP_LOSS: 'stop',
            OrderType.TRAILING_STOP: 'trailing_stop',
            OrderType.TAKE_PROFIT: 'take_profit'
        }
        return order_type_map.get(order_type, 'market')

    def _convert_to_order(self, ccxt_order: Dict) -> Order:
        return Order(
            id=ccxt_order['id'],
            symbol=ccxt_order['symbol'],
            order_type=ccxt_order['type'],
            order_side=ccxt_order['side'].upper(),
            quantity=ccxt_order['amount'],
            trail=ccxt_order.get('trailingAmount'),
            limit=ccxt_order.get('price'),
            stop=ccxt_order.get('stopPrice'),
            timestamp=datetime.fromtimestamp(ccxt_order['timestamp'] / 1000),
            status=self._convert_status(ccxt_order['status']),
            trades=[self._convert_to_trade(t) for t in ccxt_order.get('trades', [])]
        )

    def _convert_status(self, ccxt_status: str) -> str:
        status_map = {
            'closed': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELLED,
            'open': OrderStatus.PENDING,
            'partial': OrderStatus.PARTIALLY_FILLED
        }
        return status_map.get(ccxt_status, OrderStatus.PENDING)

    def _convert_to_trade(self, ccxt_trade: Dict) -> Trade:
        return Trade(
            id=ccxt_trade['id'],
            order_id=ccxt_trade['order'],
            symbol=ccxt_trade['symbol'],
            order_type=ccxt_trade['type'],
            order_side=ccxt_trade['side'].upper(),
            price=ccxt_trade['price'],
            quantity=ccxt_trade['amount'],
            timestamp=datetime.fromtimestamp(ccxt_trade['timestamp'] / 1000),
            transaction_costs=ccxt_trade.get('fee', {}).get('cost', 0)
        )
