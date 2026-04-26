from .adx_ema import AdxEmaStrategy, PARAMS as adx_ema_params
from .adx_ema_rsi import AdxEmaRsiStrategy, PARAMS as adx_ema_rsi_params
from .adx_sma_cci import AdxSmaCciStrategy, PARAMS as adx_sma_cci_params
from .simple_reversal import SimpleReversalStrategy, PARAMS as simple_reversal_params
from .sma_buy_dip import SmaBuyDipStrategy, PARAMS as sma_buy_dip_params
from .volume_climax import VolumeClimaxStrategy, PARAMS as volume_climax_params

STRATEGY_PARAMS = {
    'AdxEmaStrategy': adx_ema_params,
    'AdxEmaRsiStrategy': adx_ema_rsi_params,
    'AdxSmaCciStrategy': adx_sma_cci_params,
    'SimpleReversalStrategy': simple_reversal_params,
    'SmaBuyDipStrategy': sma_buy_dip_params,
    'VolumeClimaxStrategy': volume_climax_params,
}

__all__ = list(STRATEGY_PARAMS.keys())


def get_all_strategies():
    return __all__


def get_strategy_params(strategy_name: str) -> dict:
    return STRATEGY_PARAMS.get(strategy_name, {})