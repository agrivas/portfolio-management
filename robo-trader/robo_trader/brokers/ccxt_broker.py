import ccxt
import logging
from typing import Dict
from datetime import datetime
from robo_trader.broker import Broker, Order, OrderType, OrderStatus, Trade

logger = logging.getLogger(__name__)

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

        if quantity is None and cash_amount is not None:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            quantity = cash_amount / price
            logger.info(f"ORDER_CALC: Converted cash_amount to quantity for {symbol} | cash_amount={cash_amount}, price={price}, quantity={quantity}")

        try:
            if quantity is not None:
                logger.info(f"ORDER_ATTEMPT: Sending {order_side.upper()} {order_type} {symbol} | quantity={quantity}, order_type={ccxt_order_type}")
                ccxt_order = self.exchange.create_order(symbol, ccxt_order_type, ccxt_order_side, quantity, None, params)
                logger.info(f"ORDER_RESULT: Order filled {symbol} | filled_quantity={ccxt_order['amount']}, cost={ccxt_order.get('cost')}, avg_price={ccxt_order.get('average')}")
            else:
                raise ValueError("Either quantity or cash_amount must be provided")
            
            logger.info(f"ORDER {ccxt_order['side'].upper()} {ccxt_order['type']} {symbol} {ccxt_order['amount']}")
            return self._convert_to_order(ccxt_order)
        except ccxt.NetworkError as e:
            log_event("ERROR", "ORDER_FAILED", f"Network error on {symbol}", f"error={str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            log_event("ERROR", "ORDER_FAILED", f"Exchange error on {symbol}", f"error={str(e)}")
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

    def get_balance(self) -> dict:
        try:
            balance = self.exchange.fetch_balance()
            return {
                'free': balance.get('free', {}),
                'used': balance.get('used', {}),
                'total': balance.get('total', {})
            }
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def get_open_positions(self, symbol: str = None) -> dict:
        try:
            open_orders = self.exchange.fetch_open_orders(symbol) if symbol else self.exchange.fetch_open_orders()
            positions = {}
            for order in open_orders:
                if order['status'] == 'open':
                    positions[order['symbol']] = {
                        'quantity': order['amount'],
                        'price': order.get('price'),
                        'side': order['side']
                    }
            return positions
        except ccxt.NetworkError as e:
            raise Exception(f"Network error: {str(e)}")
        except ccxt.ExchangeError as e:
            raise Exception(f"Exchange error: {str(e)}")

    def get_cash_balance(self, quote_currency: str) -> float:
        balance = self.get_balance()
        return balance.get('free', {}).get(quote_currency, 0.0)

    def get_asset_balance(self, base_currency: str) -> float:
        balance = self.get_balance()
        return balance.get('free', {}).get(base_currency, 0.0)

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