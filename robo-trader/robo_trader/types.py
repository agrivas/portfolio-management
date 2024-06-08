# robo_trader/types.py

from enum import Enum
from dataclasses import dataclass
from json import JSONEncoder
import json

class TradeAction(Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class Ohlcv:
    DATE = 'date'
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'

# Custom JSON Encoder that handles Enums
class EnhancedJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value  # or obj.name if you prefer
        return super().default(obj)

# Set this encoder as the default for json.dumps and json.dump
json._default_encoder = EnhancedJSONEncoder()