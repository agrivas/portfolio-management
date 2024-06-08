# robo_trader/robo_trader.py

from robo_trader.price_provider import PriceProvider
from robo_trader.signal_generator import SignalGenerator
from robo_trader.portfolio_manager import PortfolioManager
from .types import Ohlcv
import time

class RoboTrader:
    def __init__(self, symbol: str, price_provider: PriceProvider, signal_generator: SignalGenerator, portfolio_manager: PortfolioManager):
        self.symbol = symbol
        self.price_provider = price_provider
        self.signal_generator = signal_generator
        self.portfolio_manager = portfolio_manager

    def run(self, exit_after: int = None):
        iterations = 0

        while True:
            latest_ohlcv = self.price_provider.get_latest_ohlcv()
            self.signal_generator.add_historical_data(
                date=latest_ohlcv[Ohlcv.DATE],
                open_price=latest_ohlcv[Ohlcv.OPEN],
                high_price=latest_ohlcv[Ohlcv.HIGH],
                low_price=latest_ohlcv[Ohlcv.LOW],
                close_price=latest_ohlcv[Ohlcv.CLOSE],
                volume=latest_ohlcv[Ohlcv.VOLUME]
            )
            print(f"Added OHLCV data: {latest_ohlcv}")
            print(self.signal_generator)

            # The model might need to update additional features
            self.signal_generator.update_prediction()

            # Generate signal
            signal = self.signal_generator.generate_signal()
            
            # Act on the signal
            self.act_on_signal(signal, latest_ohlcv[Ohlcv.CLOSE])

            # Quit after N iterations
            if exit_after is not None:
                iterations += 1
                if exit_after <= iterations:
                    break

            # Wait for 1 second before the next update
            time.sleep(1)
            

    def act_on_signal(self, signal, current_price):
        if signal == "BUY":
            print(f"Buying {self.symbol} at {current_price}")
            self.portfolio_manager.buy(price_override=current_price)
        elif signal == "SELL":
            print(f"Selling {self.symbol} at {current_price}")
            self.portfolio_manager.sell(price_override=current_price)
