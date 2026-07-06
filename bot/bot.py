"""
bot/bot.py - Main trading bot loop.
Usage: python -m bot.bot
"""

import logging
import os
import time
import yaml

from data.fetcher import fetch_ohlcv
from bot.strategy import Strategy
from bot.risk import RiskManager
from bot.executor import Executor

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/bot.log")],
)
log = logging.getLogger(__name__)

TIMEFRAME_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400,
}


def load_config(path="config/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def run():
    config = load_config()
    symbol = config["symbol"]
    timeframe = config["timeframe"]
    paper_trading = config.get("paper_trading", True)
    sleep_seconds = TIMEFRAME_SECONDS.get(timeframe, 3600)

    strategy = Strategy(config["strategy"])
    risk = RiskManager(config["risk"])
    executor = Executor(config)

    capital = 10_000.0
    position = 0.0
    entry_price = 0.0

    log.info(f"Bot started | {'PAPER' if paper_trading else 'LIVE'} | {symbol} | {timeframe}")

    while True:
        try:
            df = fetch_ohlcv(symbol, timeframe, limit=200, paper_trading=paper_trading)
            current_price = df["close"].iloc[-1]
            signal = strategy.generate_signal(df)
            log.info(f"Price: {current_price:.2f} | Signal: {signal}")

            if signal == "BUY" and position == 0.0:
                amount = risk.position_size(capital, current_price)
                executor.buy(amount, current_price)
                position, entry_price = amount, current_price
                capital -= amount * current_price
                log.info(f"BUY {amount:.6f} | SL: {risk.stop_loss_price(current_price, 'buy'):.2f} | TP: {risk.take_profit_price(current_price, 'buy'):.2f}")

            elif signal == "SELL" and position > 0.0:
                executor.sell(position, current_price)
                pnl = (current_price - entry_price) * position
                capital += position * current_price
                log.info(f"SELL | PnL: {pnl:+.2f} USDT | Capital: {capital:.2f}")
                position, entry_price = 0.0, 0.0

            elif position > 0.0:
                sl = risk.stop_loss_price(entry_price, "buy")
                tp = risk.take_profit_price(entry_price, "buy")
                if current_price <= sl or current_price >= tp:
                    reason = "Stop-loss" if current_price <= sl else "Take-profit"
                    executor.sell(position, current_price)
                    pnl = (current_price - entry_price) * position
                    capital += position * current_price
                    log.info(f"{reason} triggered | PnL: {pnl:+.2f} | Capital: {capital:.2f}")
                    position, entry_price = 0.0, 0.0

            log.info(f"Portfolio -> Cash: {capital:.2f} USDT | Position: {position:.6f}")

        except Exception as e:
            log.error(f"Error: {e}")

        log.info(f"Sleeping {sleep_seconds}s...")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    run()
