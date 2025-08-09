from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid, sys
from datetime import datetime, timedelta
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="{time} {level} {extra[correlation_id]} {message}", level="INFO")
app = FastAPI(title="Portfolio & Risk Management Service", version="1.2.0")

class Trade(BaseModel):
    ticker: str; quantity: float; price: float; action: str
    source: Optional[str] = None; trade_date: str; correlation_id: Optional[str] = None
class Portfolio(BaseModel):
    id: str; cash: float; positions: Dict[str, float] = {}; history: List[Dict] = []; total_value: float = 0.0

portfolios: Dict[str, Portfolio] = {}

def get_total_value(p: Portfolio) -> float:
    return p.cash if p.cash > 0 else 0.0

def check_risk_limits(p: Portfolio, t: Trade) -> bool:
    log = logger.bind(correlation_id=t.correlation_id)
    max_pos_pct = 0.20
    p.total_value = get_total_value(p)
    if t.action.lower() == 'buy':
        trade_val = t.quantity * t.price
        new_pos_val = p.positions.get(t.ticker, 0) * t.price + trade_val
        if new_pos_val / (p.total_value + trade_val) > max_pos_pct:
            log.warning(f"RISK_VIOLATION: Trade for {t.ticker} exceeds max position size.")
            return False
    log.info(f"Trade for {t.ticker} passed risk checks.")
    return True

@app.post("/portfolio/{portfolio_id}/trade", response_model=Portfolio)
def execute_trade(portfolio_id: str, trade: Trade, slippage: float = 0.001, commission: float = 1.0):
    log = logger.bind(correlation_id=trade.correlation_id)
    if portfolio_id not in portfolios: raise HTTPException(404, "Portfolio not found")
    p = portfolios[portfolio_id]
    if not check_risk_limits(p, trade): raise HTTPException(403, f"Trade for {trade.ticker} violates risk limits.")
    log.info(f"Executing trade: {trade.quantity} of {trade.ticker}")
    return p
# Add other endpoints here...
