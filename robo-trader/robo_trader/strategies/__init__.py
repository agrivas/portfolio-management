from .adx_ema import AdxEmaStrategy
from .adx_ema_rsi import AdxEmaRsiStrategy
from .adx_sma_cci import AdxSmaCciStrategy
from .simple_reversal import SimpleReversalStrategy
from .sma_buy_dip import SmaBuyDipStrategy
from .volume_climax import VolumeClimaxStrategy

__all__ = [
    'AdxEmaStrategy',
    'AdxEmaRsiStrategy',
    'AdxSmaCciStrategy',
    'SimpleReversalStrategy',
    'SmaBuyDipStrategy',
    'VolumeClimaxStrategy',
]

def get_all_strategies():
    return __all__