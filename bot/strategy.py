"""
bot/strategy.py
Combined RSI + Moving Average crossover strategy.

BUY  signal: RSI < oversold  AND short MA crosses ABOVE long MA
SELL signal: RSI > overbought AND short MA crosses BELOW long MA
HOLD: all other conditions
"""

import pandas as pd
import numpy as np


class Strategy:
    def __init__(self, config: dict):
        self.rsi_period = config["rsi_period"]
        self.rsi_oversold = config["rsi_oversold"]
        self.rsi_overbought = config["rsi_overbought"]
        self.ma_short = config["ma_short"]
        self.ma_long = config["ma_long"]

    def compute_rsi(self, series: pd.Series) -> pd.Series:
        """RSI using Wilder's EMA method."""
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    def compute_ma(self, series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=period).mean()

    def generate_signal(self, df: pd.DataFrame) -> str:
        """Return BUY, SELL, or HOLD."""
        df = df.copy()
        df["rsi"] = self.compute_rsi(df["close"])
        df["ma_short"] = self.compute_ma(df["close"], self.ma_short)
        df["ma_long"] = self.compute_ma(df["close"], self.ma_long)
        df.dropna(inplace=True)
        if len(df) < 2:
            return "HOLD"
        prev, curr = df.iloc[-2], df.iloc[-1]
        ma_cross_up = prev["ma_short"] <= prev["ma_long"] and curr["ma_short"] > curr["ma_long"]
        ma_cross_down = prev["ma_short"] >= prev["ma_long"] and curr["ma_short"] < curr["ma_long"]
        if curr["rsi"] < self.rsi_oversold and ma_cross_up:
            return "BUY"
        if curr["rsi"] > self.rsi_overbought and ma_cross_down:
            return "SELL"
        return "HOLD"
