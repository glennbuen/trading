"""
MarketDataProvider — the abstraction strategies and engines actually
consume. Wraps ExchangeProvider and returns a canonical OHLCV DataFrame
schema, so nothing downstream needs to know it's talking to OKX (or ccxt,
or REST, at all).

Canonical schema (columns, in this order):
    ts     int64  — candle open time, epoch milliseconds (UTC)
    dt     datetime64[ns, UTC] — same, as a timezone-aware timestamp
    open, high, low, close, volume  float64

Strategies/engines must not call ExchangeProvider or ccxt directly (§28 of
the architecture: strategy should not directly call exchange APIs).
"""

import pandas as pd

from cryptobot.data.exchange import ExchangeProvider

OHLCV_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]


def _to_dataframe(raw_rows: list) -> pd.DataFrame:
    df = pd.DataFrame(raw_rows, columns=OHLCV_COLUMNS)
    df = df.drop_duplicates(subset="ts").sort_values("ts").reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class MarketDataProvider:
    def __init__(self, exchange: ExchangeProvider):
        self.exchange = exchange

    def get_ohlcv(self, symbol: str, timeframe: str, candles: int) -> pd.DataFrame:
        """Real history via backward pagination — use for backtesting /
        research where you need `candles` real bars, not whatever a single
        exchange call happens to cap out at."""
        raw = self.exchange.fetch_ohlcv_paginated(symbol, timeframe, candles)
        return _to_dataframe(raw)

    def get_recent_ohlcv(self, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
        """Single call — use for the live/paper polling loop, where a
        rolling recent window is all that's needed and pagination latency
        would be wasteful."""
        raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return _to_dataframe(raw)

    def get_last_price(self, symbol: str) -> float:
        """Current live quote — the actual fillable price for the
        paper/live trading loop, distinct from any OHLCV candle's own
        close (always historical, at best the most recently CLOSED
        candle's close)."""
        ticker = self.exchange.fetch_ticker(symbol)
        return float(ticker["last"])
