import pytest
from datetime import datetime, timezone, timedelta
from robo_trader.strategies.lorentzian_strategy import LorentzianStrategy, LorentzianSettings, LorentzianOptimizer
from robo_trader.portfolio import Portfolio
from robo_trader.price_provider import Interval
from robo_trader.exchange import DummyExchange
from robo_trader.price_providers.yfinance import YFinancePriceProvider
import pandas as pd

SYMBOL = "BTC-GBP"

@pytest.fixture
def setup_strategy():
    price_provider = YFinancePriceProvider()
    exchange = DummyExchange({SYMBOL: 100.0}, 0.004)
    portfolio = Portfolio(SYMBOL, exchange, inception_date=datetime(2000, 1, 1, tzinfo=timezone.utc))
    settings = LorentzianSettings()
    strategy = LorentzianStrategy(SYMBOL, price_provider, Interval.ONE_HOUR, portfolio, settings)
    
    return strategy, price_provider, portfolio

def test_backtest(setup_strategy):
    strategy, _, _ = setup_strategy

    start_date = (datetime.now(timezone.utc) - timedelta(days=366)).replace(minute=0, second=0, microsecond=0)
    end_date = (datetime.now(timezone.utc) - timedelta(days=359)).replace(minute=0, second=0, microsecond=0)

    result_df = strategy.backtest(start_date, end_date, period=24)
    
    assert isinstance(result_df, pd.DataFrame)
    assert 'price_start' in result_df.columns
    assert 'price_end' in result_df.columns
    assert 'asset_return' in result_df.columns
    assert 'valuation_start' in result_df.columns
    assert 'valuation_end' in result_df.columns
    assert 'portfolio_return' in result_df.columns
    assert len(result_df) == 8  # 7 discrete returns + 1 for the whole period

def test_get_optimal_settings(setup_strategy):
    _, price_provider, portfolio = setup_strategy

    start_date = (datetime.now(timezone.utc) - timedelta(days=366)).replace(minute=0, second=0, microsecond=0)
    end_date = (datetime.now(timezone.utc) - timedelta(days=359)).replace(minute=0, second=0, microsecond=0)

    optimizer_settings = LorentzianSettings(
        neighborsCount=range(8, 9),
        maxBarsBack=[2000],
        useDynamicExits=[False],
        useEmaFilter=[False],
        emaPeriod=[200],
        useSmaFilter=[False],
        smaPeriod=[200],
        useKernelSmoothing=[False],
        lookbackWindow=[8],
        relativeWeight=[8.0],
        regressionLevel=[25],
        crossoverLag=[2],
        useVolatilityFilter=[False],
        useRegimeFilter=[False],
        useAdxFilter=[False],
        regimeThreshold=[0.0],
        adxThreshold=[0],
        use_RSI=[True],
        RSI_param1=[14],
        RSI_param2=[2],
        use_WT=[True],
        WT_param1=[10],
        WT_param2=[11],
        use_CCI=[True],
        CCI_param1=[20],
        CCI_param2=[2],
        use_ADX=[True],
        ADX_param1=[20],
        ADX_param2=[2],
        use_MFI=[True],
        MFI_param1=[14]
    )

    optimal_settings = LorentzianOptimizer.get_optimal_settings(
        SYMBOL, price_provider, Interval.ONE_HOUR, portfolio, optimizer_settings, start_date, end_date
    )

    assert isinstance(optimal_settings, LorentzianSettings)
    assert optimal_settings.neighborsCount == 8