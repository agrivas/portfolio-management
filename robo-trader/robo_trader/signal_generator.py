# robo_trader/signal_generator.py

from abc import ABC, abstractmethod
import pandas as pd

class SignalGenerator(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.historical_data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        self.historical_data.columns = map(str.lower, self.historical_data.columns)

    def add_historical_data(self, date, open_price, high_price, low_price, close_price, volume):
        new_data = pd.DataFrame([{
            'date': pd.to_datetime(date),
            'open': float(open_price),
            'high': float(high_price),
            'low': float(low_price),
            'close': float(close_price),
            'volume': float(volume)
        }])
        new_data.columns = map(str.lower, new_data.columns)
        self.historical_data = pd.concat([self.historical_data, new_data], ignore_index=True)

    @abstractmethod
    def generate_signal(self):
        pass

    @abstractmethod
    def update_prediction(self):
        pass

    def __str__(self):
        return self.historical_data.tail().to_string()
    
class DummySignalGenerator(SignalGenerator):
    def generate_signal(self):
        # Dummy implementation for generating signal
        # In real scenario, replace with actual signal generation logic
        if not self.historical_data.empty:
            latest_close = self.historical_data.iloc[-1]['close']
            # Simple logic: buy if the latest close price is below 100, sell otherwise
            if latest_close < 100:
                return "BUY"
            else:
                return "SELL"
        return None

    def update_prediction(self):
        # Dummy implementation for updating prediction
        # In real scenario, replace with actual prediction update logic
        return
