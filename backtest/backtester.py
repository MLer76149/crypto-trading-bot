"""
backtest/backtester.py - Backtest RSI+MA strategy on historical data.
Usage: python -m backtest.backtester
"""

import yaml
import numpy as np
import pandas as pd

from data.fetcher import fetch_ohlcv
from bot.strategy import Strategy


class Backtester:
    def __init__(self, config: dict):
        self.strategy = Strategy(config["strategy"])
        self.initial_capital = config["backtest"]["initial_capital"]
        self.stop_loss_pct = config["risk"]["stop_loss_pct"]
        self.take_profit_pct = config["risk"]["take_profit_pct"]
        self.max_position_size = config["risk"]["max_position_size"]
        self.trades = []
        self.equity_curve = []
        self.final_capital = self.initial_capital

    def run(self, df: pd.DataFrame):
        capital = float(self.initial_capital)
        position = 0.0
        entry_price = 0.0

        for i in range(51, len(df)):
            window = df.iloc[:i]
            signal = self.strategy.generate_signal(window)
            price = df["close"].iloc[i]

            if position > 0.0:
                sl = entry_price * (1 - self.stop_loss_pct)
                tp = entry_price * (1 + self.take_profit_pct)
                if price <= sl or price >= tp:
                    reason = "stop_loss" if price <= sl else "take_profit"
                    pnl = (price - entry_price) * position
                    capital += position * price
                    self.trades.append({"type": "sell", "reason": reason, "price": price, "pnl": pnl})
                    position, entry_price = 0.0, 0.0

            if signal == "BUY" and position == 0.0:
                amount = (capital * self.max_position_size) / price
                capital -= amount * price
                position, entry_price = amount, price
                self.trades.append({"type": "buy", "price": price, "pnl": 0})
            elif signal == "SELL" and position > 0.0:
                pnl = (price - entry_price) * position
                capital += position * price
                self.trades.append({"type": "sell", "reason": "signal", "price": price, "pnl": pnl})
                position, entry_price = 0.0, 0.0

            self.equity_curve.append(capital + position * price)

        if position > 0.0:
            price = df["close"].iloc[-1]
            pnl = (price - entry_price) * position
            capital += position * price
            self.trades.append({"type": "sell", "reason": "end", "price": price, "pnl": pnl})
            self.equity_curve.append(capital)

        self.final_capital = capital

    def report(self):
        if not self.equity_curve:
            print("No trades made.")
            return
        equity = np.array(self.equity_curve)
        total_return = (self.final_capital - self.initial_capital) / self.initial_capital * 100
        sells = [t for t in self.trades if t["type"] == "sell"]
        num_trades = len(sells)
        win_rate = len([t for t in sells if t["pnl"] > 0]) / num_trades * 100 if num_trades else 0
        peak = np.maximum.accumulate(equity)
        max_drawdown = ((equity - peak) / peak).min() * 100
        returns = np.diff(equity) / equity[:-1]
        sharpe = (returns.mean() / returns.std() * np.sqrt(8760)) if returns.std() > 0 else 0
        print("\n" + "=" * 45)
        print("       BACKTEST RESULTS")
        print("=" * 45)
        print(f"  Initial Capital : ${self.initial_capital:,.2f}")
        print(f"  Final Capital   : ${self.final_capital:,.2f}")
        print(f"  Total Return    : {total_return:+.2f}%")
        print(f"  Number of Trades: {num_trades}")
        print(f"  Win Rate        : {win_rate:.1f}%")
        print(f"  Max Drawdown    : {max_drawdown:.2f}%")
        print(f"  Sharpe Ratio    : {sharpe:.2f}")
        print("=" * 45 + "\n")


def main():
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)
    symbol, timeframe = config["symbol"], config["timeframe"]
    print(f"Fetching data for {symbol} ({timeframe})...")
    df = fetch_ohlcv(symbol, timeframe, limit=1000, paper_trading=True)
    print(f"Fetched {len(df)} candles ({df.index[0]} to {df.index[-1]})")
    bt = Backtester(config)
    bt.run(df)
    bt.report()


if __name__ == "__main__":
    main()
