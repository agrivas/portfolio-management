# tests/test_portfolio.py

from datetime import datetime, timedelta, timezone
import os
import pytest
from robo_trader.portfolio import Portfolio, DATE_FORMAT
from robo_trader.types import TradeAction
from robo_trader.exchange import DummyExchange

@pytest.fixture
def exchange():
    return DummyExchange({"XBTGBP": 100.0}, 0.004)

@pytest.fixture
def portfolio(exchange):
    return Portfolio("XBTGBP", exchange)

def test_initial_balance(portfolio: Portfolio):
    assert portfolio.cash == 1000.0

def test_buy(portfolio: Portfolio):
    # Set a specific price for the test
    test_price = 10
    portfolio.exchange.set_current_price("XBTGBP", test_price)
    
    # Perform the buy
    portfolio.buy()
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0]['action'] == TradeAction.BUY
    assert portfolio.trades[0]['price'] == test_price

    # Check final portfolio state
    assert portfolio.tokens == pytest.approx(98.6, .01)
    assert portfolio.cash == pytest.approx(10, .01)

def test_sell(portfolio: Portfolio):
    # Set a specific price for the test
    test_price = 10
    portfolio.exchange.set_current_price("XBTGBP", test_price)
    
    # Set initial tokens for the test
    portfolio.tokens = 100
    
    # Perform the sell
    portfolio.sell()
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0]['action'] == TradeAction.SELL
    assert portfolio.trades[0]['price'] == test_price

    # Check final portfolio state
    assert portfolio.tokens == pytest.approx(0)
    assert portfolio.cash == pytest.approx(1996)

def test_rebalance_sell(portfolio: Portfolio):
    # Set a specific price for the test
    test_price = 10
    portfolio.exchange.set_current_price("XBTGBP", test_price)
    
    # Set initial tokens and cash for the test
    portfolio.tokens = 100
    portfolio.cash = 500
    
    # Perform the rebalance
    portfolio.rebalance()
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    trade_action = portfolio.trades[0]['action']
    assert trade_action == TradeAction.SELL

    # Check final portfolio state
    # Depending on the rebalance, tokens and cash should have adjusted towards equilibrium
    assert portfolio.tokens == pytest.approx(75, 1)
    assert portfolio.cash == pytest.approx(750, 1)

def test_rebalance_buy(portfolio: Portfolio):
    # Set a specific price for the test
    test_price = 10
    portfolio.exchange.set_current_price("XBTGBP", test_price)
    
    # Set initial tokens and cash for the test
    portfolio.tokens = 50
    portfolio.cash = 1000
    
    # Perform the rebalance
    portfolio.rebalance()
    
    # Check if the trade was recorded correctly
    assert len(portfolio.trades) == 1
    trade_action = portfolio.trades[0]['action']
    assert trade_action == TradeAction.BUY

    # Check final portfolio state
    # Depending on the rebalance, tokens and cash should have adjusted towards equilibrium
    assert portfolio.tokens == pytest.approx(75, 1)
    assert portfolio.cash == pytest.approx(750, 1)

def test_rebalance_no_trade(portfolio: Portfolio):
    # Set a specific price for the test
    test_price = 10
    portfolio.exchange.set_current_price("XBTGBP", test_price)
    
    # Set initial tokens and cash for the test
    portfolio.tokens = 75
    portfolio.cash = 750
    
    # Perform the rebalance
    portfolio.rebalance()
    
    # Check if no trade was recorded
    assert len(portfolio.trades) == 0

    # Check final portfolio state remains unchanged
    assert portfolio.tokens == pytest.approx(75, 1)
    assert portfolio.cash == pytest.approx(750, 1)

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
    inception_date = datetime.now(timezone.utc) - timedelta(days=31)
    past_date = datetime.now(timezone.utc) - timedelta(days=30)
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


def test_state_persistance(portfolio: Portfolio, exchange: DummyExchange):
    # Save the state to a file
    portfolio.save_state()

    # Assert that the file exists
    assert os.path.exists(portfolio.filename)

    # Load the saved state from the file
    new_portfolio = Portfolio("XBTGBP", exchange)
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

    os.remove(portfolio.filename)
