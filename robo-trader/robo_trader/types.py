# robo_trader/types.py

from datetime import datetime
from dataclasses import dataclass
from json import JSONEncoder
import json

class TradeAction:
    BUY = 'BUY'
    SELL = 'SELL'

class Ohlcv:
    DATE = 'date'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'