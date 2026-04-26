from .adx import run as run_adx, PARAMS as adx_params
from .adx_ema import run as run_adx_ema, PARAMS as adx_ema_params
from .adx_ema_rsi import run as run_adx_ema_rsi, PARAMS as adx_ema_rsi_params
from .adx_sma_cci import run as run_adx_sma_cci, PARAMS as adx_sma_cci_params
from .bollinger import run as run_bollinger, PARAMS as bollinger_params
from .bollinger_supertrend import run as run_bollinger_supertrend, PARAMS as bollinger_supertrend_params
from .cci import run as run_cci, PARAMS as cci_params
from .cmf import run as run_cmf, PARAMS as cmf_params
from .macd import run as run_macd, PARAMS as macd_params
from .mfi import run as run_mfi, PARAMS as mfi_params
from .obv import run as run_obv, PARAMS as obv_params
from .rsi import run as run_rsi, PARAMS as rsi_params
from .rsi_sma_adx import run as run_rsi_sma_adx, PARAMS as rsi_sma_adx_params
from .rsi_v_recovery import run as run_rsi_v_recovery, PARAMS as rsi_v_recovery_params
from .supertrend import run as run_supertrend, PARAMS as supertrend_params
from .volume_climax import run as run_volume_climax, PARAMS as volume_climax_params
from .vwap import run as run_vwap, PARAMS as vwap_params

INDICATOR_PARAMS = {
    'run_adx': adx_params,
    'run_adx_ema': adx_ema_params,
    'run_adx_ema_rsi': adx_ema_rsi_params,
    'run_adx_sma_cci': adx_sma_cci_params,
    'run_bollinger': bollinger_params,
    'run_bollinger_supertrend': bollinger_supertrend_params,
    'run_cci': cci_params,
    'run_cmf': cmf_params,
    'run_macd': macd_params,
    'run_mfi': mfi_params,
    'run_obv': obv_params,
    'run_rsi': rsi_params,
    'run_rsi_sma_adx': rsi_sma_adx_params,
    'run_rsi_v_recovery': rsi_v_recovery_params,
    'run_supertrend': supertrend_params,
    'run_volume_climax': volume_climax_params,
    'run_vwap': vwap_params,
}

__all__ = list(INDICATOR_PARAMS.keys())

def get_all_indicators():
    return __all__


def get_indicator_params(runner_name: str) -> dict:
    """Get PARAMS dict for a given indicator runner function name."""
    return INDICATOR_PARAMS.get(runner_name, {})