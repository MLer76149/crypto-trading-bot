"""
bot/executor.py
Order execution - paper trading and live trading.
"""

import logging
import os
from datetime import datetime
import ccxt
from dotenv import load_dotenv

load_dotenv()
os.makedirs("logs", exist_ok=True)

trade_logger = logging.getLogger("trade_logger")
trade_logger.setLevel(logging.INFO)
if not trade_logger.handlers:
    fh = logging.FileHandler("logs/trades.log")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    trade_logger.addHandler(fh)


class Executor:
    def __init__(self, config: dict):
        self.paper_trading = config.get("paper_trading", True)
        self.symbol = config["symbol"]
        self.exchange = None
        if not self.paper_trading:
            self.exchange = ccxt.binance({
                "apiKey": os.getenv("BINANCE_API_KEY"),
                "secret": os.getenv("BINANCE_API_SECRET"),
                "enableRateLimit": True,
            })

    def buy(self, amount: float, price: float) -> dict:
        if self.paper_trading:
            trade_logger.info(f"[PAPER] BUY  {amount:.6f} {self.symbol} @ {price:.2f}")
            return {"side": "buy", "amount": amount, "price": price, "timestamp": datetime.utcnow().isoformat()}
        order = self.exchange.create_market_buy_order(self.symbol, amount)
        trade_logger.info(f"[LIVE]  BUY  {amount:.6f} {self.symbol} @ {price:.2f}")
        return order

    def sell(self, amount: float, price: float) -> dict:
        if self.paper_trading:
            trade_logger.info(f"[PAPER] SELL {amount:.6f} {self.symbol} @ {price:.2f}")
            return {"side": "sell", "amount": amount, "price": price, "timestamp": datetime.utcnow().isoformat()}
        order = self.exchange.create_market_sell_order(self.symbol, amount)
        trade_logger.info(f"[LIVE]  SELL {amount:.6f} {self.symbol} @ {price:.2f}")
        return order
