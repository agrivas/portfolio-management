from robo_trader.portfolio import Portfolio
from robo_trader.price_provider import PriceProvider, Interval
from robo_trader.strategy import Strategy, TradeSignal
from dataclasses import dataclass
from advanced_ta import LorentzianClassification
from ta.volume import money_flow_index as MFI
import pandas as pd
from datetime import datetime
import os
import warnings

# Suppress specific warning from numpy
warnings.filterwarnings("ignore", message="All-NaN slice encountered")

@dataclass
class LorentzianSettings:
    neighborsCount:int = 8
    maxBarsBack:int = 2000
    useDynamicExits:bool = False
    useEmaFilter:bool = False
    emaPeriod:int = 200
    useSmaFilter:bool = False
    smaPeriod:int = 200
    useKernelSmoothing:bool = False
    lookbackWindow:int = 8
    relativeWeight:float = 8.0
    regressionLevel:int = 25
    crossoverLag:int = 2
    useVolatilityFilter:bool = False
    useRegimeFilter:bool = False
    useAdxFilter:bool = False
    regimeThreshold:float = 0.0
    adxThreshold:int = 0
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

class LorentzianStrategy(Strategy):
    def __init__(self, symbol: str, price_provider: PriceProvider, interval: Interval, portfolio: Portfolio, settings: LorentzianSettings):
        super().__init__(symbol, price_provider, interval, portfolio)
        self.settings = settings
        self.last_price_point = None
        self.last_prediction = None

    def analyze_prices(self, prices):
        """
        Analyze the prices using a Lorentzian function to determine the market condition.
        This is a placeholder for the actual Lorentzian analysis.
        """

        min_data_for_adx = max(self.settings.ADX_param1, self.settings.adxThreshold) * self.settings.ADX_param2
        if (self.settings.use_ADX or self.settings.useAdxFilter) and len(prices) <= min_data_for_adx:
            return TradeSignal.REBALANCE

        lc = self.get_lorentzian_predictions(prices)        
        last_price_point_prediction = lc.data.iloc[-1]

        if not pd.isna(last_price_point_prediction['endShortTrade']) or not pd.isna(last_price_point_prediction['endLongTrade']):
            return TradeSignal.REBALANCE
        elif not pd.isna(last_price_point_prediction['startLongTrade']):
            return TradeSignal.BUY
        elif not pd.isna(last_price_point_prediction['startShortTrade']):
            return TradeSignal.SELL
        else:
            return TradeSignal.NO_ACTION

    def get_lorentzian_predictions(self, prices):
        """
        Get the prediction from the Lorentzian analysis.
        """        

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

