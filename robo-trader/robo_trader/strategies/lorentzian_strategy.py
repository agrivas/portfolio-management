from robo_trader.portfolio import Portfolio
from robo_trader.price_provider import PriceProvider, Interval
from dataclasses import dataclass
from advanced_ta import LorentzianClassification
from ta.volume import money_flow_index as MFI
import pandas as pd
from datetime import datetime

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

class LorentzianStrategy:
    def __init__(self, symbol: str, price_provider: PriceProvider, interval: Interval, portfolio: Portfolio, settings: LorentzianSettings):
        self.symbol = symbol
        self.price_provider = price_provider
        self.portfolio = portfolio
        self.settings = settings
        self.interval = interval
        self.last_price_point = None
        self.last_prediction = None

    def backtest(self, start_date: datetime, end_date: datetime, period: int = None):
        """
        Replay historical data from the price provider as if we received one point at a time.
        Track the price of the asset on the first date and the valuation of the portfolio.
        Record them again at the end of the period, calculate the returns for both and return them in a dict.
        Additionally, calculate discrete performance every 'period' prices if specified.
        """
        prices = self.price_provider.get_prices(self.symbol, self.interval, start_date, end_date)
        if prices.empty:
            print("No historical data available for backtesting.")
            return

        initial_price = prices.iloc[0]['open']
        initial_date = prices.index[0]
        initial_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=initial_price, valuation_point=initial_date)

        discrete_returns = []
        for index, price_point in enumerate(prices.itertuples(), 1):
            self.last_price_point = price_point
            self.evaluate_market(prices.iloc[:index])

            if period is not None and index % period == 0:
                current_price = price_point.close
                current_date = price_point.Index
                current_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=current_price, valuation_point=current_date)
                price_return = (current_price - initial_price) / initial_price
                portfolio_return = (current_portfolio_valuation - initial_portfolio_valuation) / initial_portfolio_valuation

                discrete_returns.append({
                    'period_end_date': current_date,
                    'current_price': current_price,
                    'price_return': price_return,
                    'current_portfolio_valuation': current_portfolio_valuation,
                    'portfolio_return': portfolio_return
                })

        final_price = prices.iloc[-1]['close']
        final_date = prices.index[-1]
        final_portfolio_valuation = self.portfolio.get_valuation(price_at_valuation=final_price, valuation_point=final_date)

        price_return = (final_price - initial_price) / initial_price
        portfolio_return = (final_portfolio_valuation - initial_portfolio_valuation) / initial_portfolio_valuation

        return {
            'initial_price': initial_price,
            'final_price': final_price,
            'price_return': price_return,
            'initial_portfolio_valuation': initial_portfolio_valuation,
            'final_portfolio_valuation': final_portfolio_valuation,
            'portfolio_return': portfolio_return,
            'discrete_returns': discrete_returns
        }

    def run(self):
        """
        Continuously evaluate the market at every minute, only if new data is available.
        """
        import time
        try:
            while True:
                prices = self.price_provider.get_prices(self.symbol, self.interval)
                if prices.empty or (self.last_price_point is not None and prices.iloc[-1].equals(self.last_price_point)):
                    print("No new data. Waiting for next interval.")
                else:
                    self.last_price_point = prices.iloc[-1]
                    self.evaluate_market(prices)
                time.sleep(60)  # Sleep for 60 seconds before the next evaluation
        except KeyboardInterrupt:
            print("Stopped the market evaluation loop.")

    def evaluate_market(self, prices):
        """
        Evaluate the market conditions based on Lorentzian analysis and decide whether to buy, sell, or rebalance.
        """
        market_condition = self.analyze_prices(prices)
                
        if market_condition == 'startLongTrade':
            self.portfolio.buy()
        elif market_condition == 'startShortTrade':
            self.portfolio.sell()
        elif market_condition in ['endLongTrade', 'endShortTrade']:
            self.portfolio.rebalance()

        self.last_prediction = market_condition

    def analyze_prices(self, prices):
        """
        Analyze the prices using a Lorentzian function to determine the market condition.
        This is a placeholder for the actual Lorentzian analysis.
        """

        if self.settings.use_ADX and len(prices) <= self.settings.ADX_param1 * self.settings.ADX_param2:
            return 'hold'

        lc = self.get_lorentzian_predictions(prices)
        last_price_point_prediction = lc.data.iloc[-1]

        if not pd.isna(last_price_point_prediction['endShortTrade']):
            return 'endShortTrade'
        elif not pd.isna(last_price_point_prediction['endLongTrade']):
            return 'endLongTrade'
        elif not pd.isna(last_price_point_prediction['startShortTrade']):
            return 'startShortTrade'
        elif not pd.isna(last_price_point_prediction['startLongTrade']):
            return 'startLongTrade'
        else:
            return 'hold'

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

