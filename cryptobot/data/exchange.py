"""
ExchangeProvider — thin, exchange-agnostic wrapper around ccxt.

This is the ONLY module in the package that talks to an exchange API.
Strategies and engines never import ccxt directly (per the architecture's
separation of MarketDataProvider from ExchangeProvider) — they consume
MarketDataProvider, which consumes this.

Contains the backward-pagination OHLCV fetcher developed and validated in
this repo's earlier standalone bots (okx_trend_bot.py etc.): OKX caps a
single fetch_ohlcv call at ~300 candles regardless of the `limit` argument,
so getting real multi-year history requires walking backward page by page.
Forward-pagination (picking a `since` up front and walking forward) was
tried first and had a real bug — if `since` predates a symbol's listing,
OKX returns an empty page and a forward walk has nothing to anchor off of.
Walking backward from "now", using only timestamps actually observed,
avoids that failure mode. See tests/test_exchange.py for the regression
test covering this.
"""

import os
import time
from dataclasses import dataclass

import ccxt


TIMEFRAME_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000,
    "12h": 43_200_000, "1d": 86_400_000, "1w": 604_800_000,
}


def timeframe_to_ms(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_MS:
        raise ValueError(f"Unsupported timeframe: {timeframe!r}")
    return TIMEFRAME_MS[timeframe]


@dataclass
class ExchangeCredentials:
    api_key: str = ""
    api_secret: str = ""
    api_passphrase: str = ""

    @classmethod
    def from_env(cls, prefix: str = "OKX") -> "ExchangeCredentials":
        return cls(
            api_key=os.getenv(f"{prefix}_API_KEY", ""),
            api_secret=os.getenv(f"{prefix}_API_SECRET", ""),
            api_passphrase=os.getenv(f"{prefix}_PASSPHRASE", ""),
        )

    def is_complete(self) -> bool:
        return bool(self.api_key and self.api_secret and self.api_passphrase)


class ExchangeProvider:
    """
    Wraps a single ccxt exchange instance. Defaults to OKX spot to match
    the rest of this repo, but nothing here is OKX-specific beyond that
    default — pass a different `exchange_id` for another ccxt-supported
    exchange.
    """

    def __init__(self, exchange_id: str = "okx", live: bool = False, demo: bool = False,
                 credentials: ExchangeCredentials | None = None):
        if live and demo:
            raise ValueError("Choose live OR demo, not both.")

        params = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
        if live or demo:
            creds = credentials or ExchangeCredentials.from_env(exchange_id.upper())
            if not creds.is_complete():
                raise RuntimeError(
                    f"Live/demo trading requires {exchange_id.upper()}_API_KEY / "
                    f"_API_SECRET / _PASSPHRASE env vars."
                )
            params.update({
                "apiKey": creds.api_key,
                "secret": creds.api_secret,
                "password": creds.api_passphrase,
            })

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(params)
        self.exchange_id = exchange_id
        self.live = live
        self.demo = demo

        if demo:
            self.exchange.set_sandbox_mode(True)

    def milliseconds(self) -> int:
        return self.exchange.milliseconds()

    @property
    def rate_limit_ms(self) -> int:
        return self.exchange.rateLimit

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 300,
                     since: int | None = None) -> list:
        """Single raw call. Exchanges commonly cap this well below `limit`
        (OKX: ~300) — callers needing real history should use
        fetch_ohlcv_paginated instead."""
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)

    def fetch_ohlcv_paginated(self, symbol: str, timeframe: str, target_candles: int,
                               limit_per_call: int = 300) -> list:
        """
        Walk BACKWARD from "now": fetch the most recent page, then use the
        oldest timestamp seen so far to request the page before it,
        repeating until target_candles are collected or a page stops
        moving further back (== reached the start of the symbol's listing
        history, or of the exchange's retained history at this
        resolution).
        """
        tf_ms = timeframe_to_ms(timeframe)
        all_rows = []
        seen_ts = set()
        cursor = None
        while len(all_rows) < target_candles:
            since = None if cursor is None else cursor - limit_per_call * tf_ms
            batch = self.fetch_ohlcv(symbol, timeframe, limit=limit_per_call, since=since)
            if not batch:
                break
            new_rows = [r for r in batch if r[0] not in seen_ts]
            if not new_rows:
                break
            seen_ts.update(r[0] for r in new_rows)
            all_rows.extend(new_rows)
            oldest_ts = batch[0][0]
            if cursor is not None and oldest_ts >= cursor:
                break
            cursor = oldest_ts
            if len(batch) < limit_per_call:
                break
            time.sleep(self.rate_limit_ms / 1000)

        all_rows.sort(key=lambda r: r[0])
        if len(all_rows) > target_candles:
            all_rows = all_rows[-target_candles:]
        return all_rows

    def fetch_ticker(self, symbol: str) -> dict:
        """Live quote — used by the paper/live trading loop to get a
        current fillable price, distinct from `fetch_ohlcv`'s historical
        candles (whose last row is the most recently CLOSED bar, not a
        fillable "right now" price)."""
        return self.exchange.fetch_ticker(symbol)

    def fetch_balance(self) -> dict:
        return self.exchange.fetch_balance()

    def fetch_open_orders(self, symbol: str) -> list:
        return self.exchange.fetch_open_orders(symbol)

    def create_order(self, symbol: str, order_type: str, side: str, amount: float) -> dict:
        return self.exchange.create_order(symbol, order_type, side, amount)
