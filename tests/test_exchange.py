import pytest

from cryptobot.data.exchange import ExchangeProvider, ExchangeCredentials, timeframe_to_ms


class FakeCcxtExchange:
    """Minimal stand-in for a ccxt exchange instance, driven by a list of
    (ts, o, h, l, c, v) rows representing ALL the history that 'exists'.
    fetch_ohlcv slices out of it the way a real exchange would, capped at
    `page_cap` per call — no network involved."""

    rateLimit = 1  # ms, keep tests fast

    def __init__(self, all_rows: list, page_cap: int = 300):
        self.all_rows = sorted(all_rows, key=lambda r: r[0])
        self.page_cap = page_cap
        self.calls = []

    def fetch_ohlcv(self, symbol, timeframe=None, since=None, limit=300):
        self.calls.append({"since": since, "limit": limit})
        limit = min(limit, self.page_cap)
        if since is None:
            return self.all_rows[-limit:]
        rows = [r for r in self.all_rows if r[0] >= since]
        return rows[:limit]

    def milliseconds(self):
        return self.all_rows[-1][0] if self.all_rows else 0


def make_rows(n: int, tf_ms: int, start: int = 0) -> list:
    return [[start + i * tf_ms, 1, 2, 0, 1, 100] for i in range(n)]


def provider_with_fake(fake: FakeCcxtExchange) -> ExchangeProvider:
    provider = ExchangeProvider(exchange_id="okx", live=False, demo=False)
    provider.exchange = fake
    return provider


class TestPagination:
    def test_collects_target_across_multiple_pages(self):
        tf_ms = timeframe_to_ms("1h")
        rows = make_rows(1000, tf_ms)
        fake = FakeCcxtExchange(rows, page_cap=300)
        provider = provider_with_fake(fake)

        result = provider.fetch_ohlcv_paginated("BTC/USDT", "1h", target_candles=700)

        assert len(result) == 700
        timestamps = [r[0] for r in result]
        assert timestamps == sorted(timestamps)
        assert len(set(timestamps)) == len(timestamps)  # no duplicates
        # Should be the MOST RECENT 700, not the oldest 700.
        assert timestamps[-1] == rows[-1][0]

    def test_stops_gracefully_at_start_of_listing_history(self):
        """Regression test for the bug found and fixed mid-project:
        forward-pagination (picking `since` up front) breaks when `since`
        predates the symbol's listing — the exchange returns an empty
        page and a forward walk has nothing to anchor off of. Backward
        pagination must instead return whatever real history exists."""
        tf_ms = timeframe_to_ms("1d")
        rows = make_rows(250, tf_ms)  # symbol only has 250 days of history
        fake = FakeCcxtExchange(rows, page_cap=300)
        provider = provider_with_fake(fake)

        result = provider.fetch_ohlcv_paginated("SOL/USDT", "1d", target_candles=3000)

        assert len(result) == 250  # got everything that exists, not 3000, and didn't hang
        assert result[0][0] == rows[0][0]
        assert result[-1][0] == rows[-1][0]

    def test_respects_the_exchanges_per_call_cap(self):
        """Even though callers can request any target_candles, no single
        underlying fetch_ohlcv call should ask for more than the
        exchange's real per-call cap suggests is achievable — verified
        indirectly: every call's limit param must equal limit_per_call."""
        tf_ms = timeframe_to_ms("1h")
        rows = make_rows(1000, tf_ms)
        fake = FakeCcxtExchange(rows, page_cap=300)
        provider = provider_with_fake(fake)

        provider.fetch_ohlcv_paginated("BTC/USDT", "1h", target_candles=650, limit_per_call=300)

        assert all(call["limit"] == 300 for call in fake.calls)
        assert len(fake.calls) >= 3  # 650 candles needs at least 3 pages of 300

    def test_exact_target_smaller_than_one_page(self):
        tf_ms = timeframe_to_ms("1h")
        rows = make_rows(1000, tf_ms)
        fake = FakeCcxtExchange(rows, page_cap=300)
        provider = provider_with_fake(fake)

        result = provider.fetch_ohlcv_paginated("BTC/USDT", "1h", target_candles=50)

        assert len(result) == 50
        assert result[-1][0] == rows[-1][0]


class TestCredentials:
    def test_incomplete_credentials_detected(self):
        creds = ExchangeCredentials(api_key="k", api_secret="", api_passphrase="p")
        assert not creds.is_complete()

    def test_complete_credentials_detected(self):
        creds = ExchangeCredentials(api_key="k", api_secret="s", api_passphrase="p")
        assert creds.is_complete()

    def test_live_without_credentials_raises(self):
        with pytest.raises(RuntimeError):
            ExchangeProvider(exchange_id="okx", live=True,
                              credentials=ExchangeCredentials())

    def test_live_and_demo_together_rejected(self):
        with pytest.raises(ValueError):
            ExchangeProvider(exchange_id="okx", live=True, demo=True)


class TestTimeframeConversion:
    def test_known_timeframes(self):
        assert timeframe_to_ms("1m") == 60_000
        assert timeframe_to_ms("1h") == 3_600_000
        assert timeframe_to_ms("1d") == 86_400_000

    def test_unknown_timeframe_raises(self):
        with pytest.raises(ValueError):
            timeframe_to_ms("7x")
