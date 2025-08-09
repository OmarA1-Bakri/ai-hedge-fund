import pytest
# Mock classes to avoid full import from service
class Portfolio:
    def __init__(self, id, cash, positions, total_value):
        self.id, self.cash, self.positions, self.total_value = id, cash, positions, total_value
class Trade:
    def __init__(self, ticker, quantity, price, action, trade_date, correlation_id=None):
        self.ticker, self.quantity, self.price, self.action, self.trade_date, self.correlation_id = ticker, quantity, price, action, trade_date, correlation_id

# In a real setup, this would import the actual function
def check_risk_limits(p: Portfolio, t: Trade) -> bool:
    max_pos_pct = 0.20
    if t.action.lower() == 'buy':
        trade_val = t.quantity * t.price
        new_pos_val = p.positions.get(t.ticker, 0) * t.price + trade_val
        if (p.total_value + trade_val) == 0: return True # Avoid division by zero
        if new_pos_val / (p.total_value + trade_val) > max_pos_pct: return False
    return True

def test_risk_pass():
    p = Portfolio("test", 80000, {"AAPL": 10000}, 90000)
    t = Trade("GOOG", 20, 100, "buy", "2023-01-01")
    assert check_risk_limits(p, t) == True

def test_risk_fail():
    p = Portfolio("test", 80000, {}, 80000)
    t = Trade("TSLA", 100, 250, "buy", "2023-01-01")
    assert check_risk_limits(p, t) == False
