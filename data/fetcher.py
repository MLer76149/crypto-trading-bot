"""
data/fetcher.py
Fetches OHLCV data from Binance using ccxt.
"""

import os
import ccxt
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_exchange(paper_trading: bool = True) -> ccxt.Exchange:
    params = {"enableRateLimit": True}
    if not paper_trading:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        if not api_key or not api_secret:
            raise ValueError("Set BINANCE_API_KEY and BINANCE_API_SECRET in .env for live trading.")
        params["apiKey"] = api_key
        params["secret"] = api_secret
    return ccxt.binance(params)


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 200, paper_trading: bool = True) -> pd.DataFrame:
    """Fetch OHLCV data. Returns DataFrame indexed by timestamp."""
    exchange = get_exchange(paper_trading)
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df.astype(float)
