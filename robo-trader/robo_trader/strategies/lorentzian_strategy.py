from robo_trader.strategy import Strategy
from robo_trader.portfolio import Portfolio
from dataclasses import dataclass
from advanced_ta import LorentzianClassification
from ta.volume import money_flow_index as MFI
import pandas as pd
import warnings
from typing import Optional
from robo_trader.trader import Trader

# Suppress specific warning from numpy
warnings.filterwarnings("ignore", message="All-NaN slice encountered")

@dataclass
class LorentzianSettings:
    neighborsCount:int = 8
    maxBarsBack:int = 2000
    
    use_RSI:bool = True
    RSI_param1:int = 14
    RSI_param2:int = 2    

    use_WT:bool = True
    WT_param1:int = 10
    WT_param2:int = 11

    use_CCI:bool = True
    CCI_param1:int = 20
    CCI_param2:int = 2

    use_ADX:bool = True
    ADX_param1:int = 20
    ADX_param2:int = 2

    use_MFI:bool = True
    MFI_param1:int = 14

    useKernelSmoothing:bool = False
    lookbackWindow:int = 8
    relativeWeight:float = 8.0
    regressionLevel:int = 25
    crossoverLag:int = 2

    useRegimeFilter:bool = False
    regimeThreshold:float = -0.1

    useAdxFilter:bool = False
    adxThreshold:int = 20

    useVolatilityFilter:bool = False
    
    useEmaFilter:bool = False
    emaPeriod:int = 200

    useSmaFilter:bool = False
    smaPeriod:int = 200
    
    useDynamicExits:bool = False

    # New parameters for position sizing and trailing stop
    position_size:float = 0.25
    trailing_stop:float = 0.01

@dataclass
class LorentzianOptimizerSettings:
    neighborsCount: Optional[range] = None
    maxBarsBack: Optional[range] = None
    
    use_RSI: Optional[range] = None
    RSI_param1: Optional[range] = None
    RSI_param2: Optional[range] = None    

    use_WT: Optional[range] = None
    WT_param1: Optional[range] = None
    WT_param2: Optional[range] = None

    use_CCI: Optional[range] = None
    CCI_param1: Optional[range] = None
    CCI_param2: Optional[range] = None

    use_ADX: Optional[range] = None
    ADX_param1: Optional[range] = None
    ADX_param2: Optional[range] = None

    use_MFI: Optional[range] = None
    MFI_param1: Optional[range] = None

    useKernelSmoothing: Optional[range] = None
    lookbackWindow: Optional[range] = None
    relativeWeight: Optional[range] = None
    regressionLevel: Optional[range] = None
    crossoverLag: Optional[range] = None

    useRegimeFilter: Optional[range] = None
    regimeThreshold: Optional[range] = None

    useAdxFilter: Optional[range] = None
    adxThreshold: Optional[range] = None

    useVolatilityFilter: Optional[range] = None
    
    useEmaFilter: Optional[range] = None
    emaPeriod: Optional[range] = None

    useSmaFilter: Optional[range] = None
    smaPeriod: Optional[range] = None
    
    useDynamicExits: Optional[range] = None

    # New optimizer settings for position sizing and trailing stop
    position_size: Optional[range] = None
    trailing_stop: Optional[range] = None

class LorentzianStrategy(Strategy):
    def __init__(self, settings: LorentzianSettings):
        super().__init__()
        self.settings = settings

    def evaluate_market(self, symbol: str, prices: pd.DataFrame, portfolio: Portfolio):
        min_data_for_adx = max(self.settings.ADX_param1, self.settings.adxThreshold) * self.settings.ADX_param2
        if (self.settings.use_ADX or self.settings.useAdxFilter) and len(prices) <= min_data_for_adx:
            return

        lc = self.get_lorentzian_predictions(prices)        
        last_price_point_prediction = lc.data.iloc[-1]

        #if not pd.isna(last_price_point_prediction['endLongTrade']):
            #portfolio.close_long(symbol)
        #elif not pd.isna(last_price_point_prediction['startLongTrade']):
        if not pd.isna(last_price_point_prediction['startLongTrade']):
            portfolio.open_long(symbol, self.settings.position_size, self.settings.trailing_stop)

    def get_lorentzian_predictions(self, prices):
        features = []
        if self.settings.use_RSI:
            features.append(LorentzianClassification.Feature("RSI", self.settings.RSI_param1, self.settings.RSI_param2))
        if self.settings.use_WT:
            features.append(LorentzianClassification.Feature("WT", self.settings.WT_param1, self.settings.WT_param2))
        if self.settings.use_CCI:
            features.append(LorentzianClassification.Feature("CCI", self.settings.CCI_param1, self.settings.CCI_param2))
        if self.settings.use_ADX:
            features.append(LorentzianClassification.Feature("ADX", self.settings.ADX_param1, self.settings.ADX_param2))
        if self.settings.use_MFI:
            features.append(MFI(prices['high'], prices['low'], prices['close'], prices['volume'], self.settings.MFI_param1))

        lc = LorentzianClassification(
            prices,    
            features,
            settings=LorentzianClassification.Settings(
                source='close',
                neighborsCount=self.settings.neighborsCount,
                maxBarsBack=self.settings.maxBarsBack,
                useDynamicExits=self.settings.useDynamicExits
            ),
            filterSettings=LorentzianClassification.FilterSettings(
                useVolatilityFilter=self.settings.useVolatilityFilter,
                useRegimeFilter=self.settings.useRegimeFilter,
                useAdxFilter=self.settings.useAdxFilter,
                regimeThreshold=self.settings.regimeThreshold,
                adxThreshold=self.settings.adxThreshold,
                kernelFilter = LorentzianClassification.KernelFilter(
                    useKernelSmoothing = self.settings.useKernelSmoothing,
                    lookbackWindow = self.settings.lookbackWindow,
                    relativeWeight = self.settings.relativeWeight,
                    regressionLevel = self.settings.regressionLevel,
                    crossoverLag = self.settings.crossoverLag
                )
            )
        )

        return lc

class LorentzianOptimizer:
    @staticmethod
    def optimize_setting(symbol, initial_capital, feed, setting_name, value_range, current_settings, start_date=None, end_date=None, period=None, train_since=None):
        best_value = None
        best_return = float('-inf')
        
        for value in value_range:
            print(f'    Testing {value} for {setting_name}')

            # Update the current setting with the new value
            updated_settings = {**current_settings, setting_name: value}
            print(f"        Updated settings: {updated_settings}")
            settings = LorentzianSettings(**updated_settings)
            strategy = LorentzianStrategy(settings)
            trader = Trader(symbol, initial_capital, feed, strategy)
            result = trader.backtest(start_date, end_date, period, train_since)
            mean_return = result['returns']['portfolio_return'].mean()
            print(f"        Mean return: {mean_return}")
            
            if mean_return > best_return:
                best_return = mean_return
                best_value = value            
        
        return best_value

    @staticmethod
    def get_optimal_settings(symbol, initial_capital, feed, optimizer_settings: LorentzianOptimizerSettings, default_settings: LorentzianSettings = None, start_date=None, end_date=None, period=None, train_since=None):
        if default_settings:
            optimal_settings_dict = default_settings.__dict__.copy()
        else:
            optimal_settings_dict = {}
        
        for setting_name, value_range in optimizer_settings.__dict__.items():
            if value_range:  # Check if a range is provided
                if len(value_range) == 1:
                    optimal_value = value_range[0]
                else:
                    optimal_value = LorentzianOptimizer.optimize_setting(symbol, initial_capital, feed, setting_name, value_range, optimal_settings_dict, start_date, end_date, period, train_since)
                print(f"Optimal value for {setting_name} is {optimal_value}")
                optimal_settings_dict[setting_name] = optimal_value
        
        return LorentzianSettings(**optimal_settings_dict)

