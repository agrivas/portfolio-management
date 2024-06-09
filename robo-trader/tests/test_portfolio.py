# tests/test_portfolio.py

from datetime import datetime, timedelta
import os
import pytest
from robo_trader.portfolio import Portfolio, DATE_FORMAT
from robo_trader.types import TradeAction
from robo_trader.exchange import DummyExchange

@pytest.fixture
def portfolio():
    return Portfolio("XBTGBP", DummyExchange({"XBTGBP": 100.0}))

def test_initial_balance(portfolio: Portfolio):
    assert portfolio.cash == 1000.0

def test_backtest_buy(portfolio: Portfolio):
    # Set a specific price and date for the backtest
    backtest_price = 10
    backtest_date = datetime.now() - timedelta(days=10)
    
    # Perform the backtest buy
    portfolio.backtest_buy(backtest_price, backtest_date)
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0]['action'] == TradeAction.BUY
    assert portfolio.trades[0]['trade_amount'] == 98.60557768924303
    assert portfolio.trades[0]['price'] == backtest_price
    assert portfolio.trades[0]['date'] == backtest_date.strftime(DATE_FORMAT)
    assert portfolio.trades[0]['cost'] == 3.9442231075697216
    assert portfolio.trades[0]['current_tokens'] == 98.60557768924303
    assert portfolio.trades[0]['current_cash'] == 9.999999999999886

    # Check final portfolio state
    assert portfolio.cash == 9.999999999999886
    assert portfolio.tokens == 98.60557768924303

def test_backtest_sell(portfolio: Portfolio):
    # Set a specific price and date for the backtest
    backtest_price = 10
    backtest_date = datetime.now() - timedelta(days=5)
    
    # Set initial tokens for the test
    portfolio.tokens = 100
    
    # Perform the backtest sell
    portfolio.backtest_sell(backtest_price, backtest_date)
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0]['action'] == TradeAction.SELL
    assert portfolio.trades[0]['trade_amount'] == 100
    assert portfolio.trades[0]['price'] == backtest_price
    assert portfolio.trades[0]['date'] == backtest_date.strftime(DATE_FORMAT)
    assert portfolio.trades[0]['cost'] == 4
    assert portfolio.trades[0]['current_tokens'] == 0
    assert portfolio.trades[0]['current_cash'] == 1996.0

    # Check final portfolio state
    assert portfolio.cash == 1996.0
    assert portfolio.tokens == 0


def test_get_current_price(portfolio: Portfolio):
    assert portfolio.get_current_price() == 100

def test_get_portfolio_valuation_current(portfolio: Portfolio):
    portfolio.buy()
    actual = portfolio.get_valuation()
    expected = portfolio.initial_cash * (1 - portfolio.transaction_costs)
    assert actual == pytest.approx(expected, 0.1)
    
    portfolio.sell()
    expected = actual - (actual * .5 * portfolio.transaction_costs) # cost of selling half of the tokens to rebalance portfolio
    assert portfolio.get_valuation() == pytest.approx(expected, 0.1)

def test_get_portfolio_valuation_past(portfolio: Portfolio):
    # Set a past date for valuation
    inception_date = datetime.now() - timedelta(days=31)
    past_date = datetime.now() - timedelta(days=30)
    past_price = 80  # Assume the price was 80 at the past date

    portfolio.inception_date = inception_date
    # Simulate a trade that happened in the past
    portfolio.trades.append({
        'action': 'BUY',
        'trade_amount': 5,
        'price': past_price,
        'date': past_date.strftime(DATE_FORMAT),
        'cost': portfolio.calculate_trade_cost(5, past_price),
        'current_tokens': 5,
        'current_cash': portfolio.initial_cash - (5 * past_price * (1 + portfolio.transaction_costs))
    })

    # Update portfolio to reflect the past trade
    portfolio.tokens = 5
    portfolio.cash = portfolio.initial_cash - (5 * past_price * (1 + portfolio.transaction_costs))

    # Calculate valuation at the past date
    valuation = portfolio.get_valuation(price_at_valuation=past_price, valuation_point=past_date)
    expected_valuation = portfolio.cash + (portfolio.tokens * past_price)

    assert abs(valuation - expected_valuation) < 0.1, "The past valuation calculation is incorrect."


def test_state_persistance(portfolio: Portfolio):
    # Save the state to a file
    portfolio.save_state()

    # Assert that the file exists
    assert os.path.exists(portfolio.filename)

    # Load the saved state from the file
    new_portfolio = Portfolio("XBTGBP", DummyExchange({"XBTGBP": 100.0}))
    new_portfolio.load_state()

    # Assert that the loaded state matches the original state
    assert new_portfolio.symbol == portfolio.symbol
    assert new_portfolio.initial_cash == portfolio.initial_cash
    assert new_portfolio.initial_tokens == portfolio.initial_tokens
    assert new_portfolio.transaction_costs == portfolio.transaction_costs
    assert new_portfolio.stop_loss_percentage == portfolio.stop_loss_percentage
    assert new_portfolio.cash_reserve_percentage == portfolio.cash_reserve_percentage
    assert new_portfolio.cash == portfolio.cash
    assert new_portfolio.tokens == portfolio.tokens
    assert new_portfolio.inception_date.strftime(DATE_FORMAT) == portfolio.inception_date.strftime(DATE_FORMAT)
    assert new_portfolio.trades == portfolio.trades
    assert new_portfolio.filename == portfolio.filename