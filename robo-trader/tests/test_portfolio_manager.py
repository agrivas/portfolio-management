# tests/test_portfolio_manager.py

from datetime import datetime
import os
import pandas as pd
import pytest
from robo_trader.portfolio_manager import PortfolioManager, DATE_FORMAT
from robo_trader.types import TradeAction, Ohlcv

@pytest.fixture
def portfolio_manager():
    return PortfolioManager("XBTGBP")

def test_initial_balance(portfolio_manager: PortfolioManager):
    assert portfolio_manager.cash == 1000.0

def test_buy(portfolio_manager: PortfolioManager):
    portfolio_manager.buy()
    assert portfolio_manager.tokens - 10 * (1 - portfolio_manager.transaction_costs) < 0.001 
    assert portfolio_manager.cash == 0
    assert len(portfolio_manager.trades) == 1
    assert 'current_tokens' in portfolio_manager.trades[0]
    assert 'current_cash' in portfolio_manager.trades[0]

def test_sell_while_in_open_long(portfolio_manager: PortfolioManager):
    portfolio_manager.initial_tokens = 20
    portfolio_manager.tokens = portfolio_manager.initial_tokens
    portfolio_manager.sell()
    assert portfolio_manager.tokens == 15.0
    assert portfolio_manager.cash == 1000 + 500 * (1 - portfolio_manager.transaction_costs)
    assert len(portfolio_manager.trades) == 1
    assert 'current_tokens' in portfolio_manager.trades[0]
    assert 'current_cash' in portfolio_manager.trades[0]

def test_sell_not_in_trade(portfolio_manager: PortfolioManager):
    portfolio_manager.initial_tokens = 10
    portfolio_manager.tokens = portfolio_manager.initial_tokens
    portfolio_manager.sell()
    assert portfolio_manager.tokens == 0
    assert portfolio_manager.cash == 1000 + 1000 * (1 - portfolio_manager.transaction_costs)
    assert len(portfolio_manager.trades) == 1
    assert 'current_tokens' in portfolio_manager.trades[0]
    assert 'current_cash' in portfolio_manager.trades[0]

def test_get_current_price(portfolio_manager: PortfolioManager):
    assert portfolio_manager.get_current_price() == 100
    assert portfolio_manager.get_current_price(10) == 10

def test_get_portfolio_value(portfolio_manager: PortfolioManager):
    portfolio_manager.buy()
    actual = portfolio_manager.get_portfolio_value()
    expected = portfolio_manager.initial_cash * (1 - portfolio_manager.transaction_costs)
    assert abs(actual - expected) < 0.1 
    
    portfolio_manager.sell()
    expected = actual - (actual * .5 * portfolio_manager.transaction_costs) # cost of selling half of the tokens to rebalance portfolio
    assert abs(portfolio_manager.get_portfolio_value() - expected) < 0.1 

def test_calculate_performance(portfolio_manager: PortfolioManager):
    portfolio_manager.inception_date = datetime(2022, 1, 1)

    # Create a sample period DataFrame for testing
    period_data = {
        Ohlcv.DATE: ['2022-01-01', '2022-01-02', '2022-01-03'],
        Ohlcv.OPEN: [100, 110, 120],
        Ohlcv.CLOSE: [105, 115, 125]
    }
    period_df = pd.DataFrame(period_data)
    period_df[Ohlcv.DATE] = pd.to_datetime(period_df[Ohlcv.DATE])
    period_df.set_index(Ohlcv.DATE, inplace=True)

    # Add some trades to the portfolio manager
    portfolio_manager.trades = [
        {'action': TradeAction.BUY, 'trade_amount': 10, 'price': 100, 'date': '2021-12-31 00:00:00', 'cost': 40, 'current_tokens': 10, 'current_cash': 600},
        {'action': TradeAction.SELL, 'trade_amount': 5, 'price': 105, 'date': '2022-01-02 00:00:00', 'cost': 20, 'current_tokens': 5, 'current_cash': 700}
    ]

    # Calculate the expected performance
    opening_price = period_df.iloc[0][Ohlcv.OPEN]
    closing_price = period_df.iloc[-1][Ohlcv.CLOSE]
    start_value = 600 + (10 * opening_price)
    end_value = 700 + (5 * closing_price)
    expected_performance = ((end_value - start_value) / start_value) * 100

    # Calculate the actual performance using the portfolio manager
    actual_performance = portfolio_manager.calculate_performance(period_df)

    # Assert that the actual performance matches the expected performance
    assert abs(actual_performance - expected_performance) < 0.001# tests/test_portfolio_manager.py

def test_state_persistance(portfolio_manager: PortfolioManager):
    # Save the state to a file
    portfolio_manager.save_state()

    # Assert that the file exists
    assert os.path.exists(portfolio_manager.filename)

    # Load the saved state from the file
    new_portfolio_manager = PortfolioManager("XBTGBP")
    new_portfolio_manager.load_state()

    # Assert that the loaded state matches the original state
    assert new_portfolio_manager.symbol == portfolio_manager.symbol
    assert new_portfolio_manager.initial_cash == portfolio_manager.initial_cash
    assert new_portfolio_manager.initial_tokens == portfolio_manager.initial_tokens
    assert new_portfolio_manager.transaction_costs == portfolio_manager.transaction_costs
    assert new_portfolio_manager.stop_loss_percentage == portfolio_manager.stop_loss_percentage
    assert new_portfolio_manager.cash_reserve_percentage == portfolio_manager.cash_reserve_percentage
    assert new_portfolio_manager.cash == portfolio_manager.cash
    assert new_portfolio_manager.tokens == portfolio_manager.tokens
    assert new_portfolio_manager.inception_date.strftime(DATE_FORMAT) == portfolio_manager.inception_date.strftime(DATE_FORMAT)
    assert new_portfolio_manager.trades == portfolio_manager.trades
    assert new_portfolio_manager.filename == portfolio_manager.filename