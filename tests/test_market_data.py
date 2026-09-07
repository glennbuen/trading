"""Tests for cryptobot/data/market_data.py's live/paper-loop helpers
(get_recent_ohlcv, get_last_price) — the paginated-history path
(get_ohlcv) is already covered indirectly via every strategy evaluation
script; these are new and specific to the paper trading engine."""

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider


class FakeExchange:
    def __init__(self, rows, last_price):
        self.rows = rows
        self.last_price = last_price
        self.fetch_ohlcv_calls = []

    def fetch_ohlcv(self, symbol, timeframe=None, since=None, limit=300):
        self.fetch_ohlcv_calls.append({"symbol": symbol, "timeframe": timeframe, "limit": limit})
        return self.rows[-limit:]

    def fetch_ticker(self, symbol):
        return {"symbol": symbol, "last": self.last_price}


def make_provider(fake: FakeExchange) -> MarketDataProvider:
    ex = ExchangeProvider(exchange_id="okx", live=False, demo=False)
    ex.exchange = fake
    return MarketDataProvider(ex)


class TestGetRecentOhlcv:
    def test_single_call_returns_canonical_dataframe(self):
        rows = [[i * 60_000, 1.0, 2.0, 0.5, 1.5, 100.0] for i in range(10)]
        fake = FakeExchange(rows, last_price=1.5)
        md = make_provider(fake)
        df = md.get_recent_ohlcv("BTC/USDT", "1m", limit=5)
        assert list(df.columns) == ["ts", "dt", "open", "high", "low", "close", "volume"]
        assert len(df) == 5
        assert len(fake.fetch_ohlcv_calls) == 1  # single call, no pagination


class TestGetLastPrice:
    def test_returns_the_tickers_last_price_as_a_float(self):
        fake = FakeExchange(rows=[], last_price=42123.45)
        md = make_provider(fake)
        assert md.get_last_price("BTC/USDT") == 42123.45
        assert isinstance(md.get_last_price("BTC/USDT"), float)
