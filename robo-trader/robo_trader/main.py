# main.py

from robo_trader.signal_generator import SignalGenerator
from robo_trader.robo_trader import RoboTrader
from robo_trader.portfolio_manager import PortfolioManager

if __name__ == "__main__":
    symbol = "XBTGBP"
    signal_generator = SignalGenerator(symbol)
    portfolio_manager = PortfolioManager(symbol)
    trader = RoboTrader(symbol, signal_generator, portfolio_manager)
    trader.run()
