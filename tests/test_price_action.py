import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import price_action as pa


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def flat_bars(n: int, rng_size: float = 2.0, base: float = 100.0) -> list[dict]:
    """n boring bars of constant small range, used as a quiet baseline so
    a single 'strong'/'breakout' bar reads as clearly larger by
    comparison."""
    return [{"open": base, "high": base + rng_size / 2, "low": base - rng_size / 2,
              "close": base, "volume": 10} for _ in range(n)]


class TestCandleShape:
    def test_strong_bullish_candle(self):
        rows = flat_bars(25) + [{"open": 100, "close": 110, "high": 111, "low": 99, "volume": 10}]
        df = make_df(rows)
        result = pa.is_strong_bullish(df, lookback=20)
        assert result.iloc[-1]
        assert not result.iloc[0]

    def test_strong_bearish_candle(self):
        rows = flat_bars(25) + [{"open": 110, "close": 100, "high": 111, "low": 99, "volume": 10}]
        df = make_df(rows)
        result = pa.is_strong_bearish(df, lookback=20)
        assert result.iloc[-1]

    def test_doji_is_not_strong_either_way(self):
        rows = flat_bars(25) + [{"open": 100, "close": 100.1, "high": 105, "low": 95, "volume": 10}]
        df = make_df(rows)
        assert not pa.is_strong_bullish(df, lookback=20).iloc[-1]
        assert not pa.is_strong_bearish(df, lookback=20).iloc[-1]

    def test_bullish_rejection_long_lower_wick(self):
        rows = flat_bars(5) + [{"open": 100, "close": 101, "high": 102, "low": 90, "volume": 10}]
        df = make_df(rows)
        assert pa.is_bullish_rejection(df).iloc[-1]
        assert not pa.is_bearish_rejection(df).iloc[-1]

    def test_bearish_rejection_long_upper_wick(self):
        rows = flat_bars(5) + [{"open": 100, "close": 99, "high": 112, "low": 98, "volume": 10}]
        df = make_df(rows)
        assert pa.is_bearish_rejection(df).iloc[-1]
        assert not pa.is_bullish_rejection(df).iloc[-1]

    def test_inside_candle(self):
        rows = [
            {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 10},
            {"open": 102, "close": 103, "high": 106, "low": 98, "volume": 10},  # inside bar 1's range
        ]
        df = make_df(rows)
        result = pa.is_inside_candle(df)
        assert not result.iloc[0]  # no prior bar
        assert result.iloc[1]

    def test_not_inside_candle_when_it_pokes_out(self):
        rows = [
            {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 10},
            {"open": 102, "close": 103, "high": 112, "low": 98, "volume": 10},  # high pokes above
        ]
        df = make_df(rows)
        assert not pa.is_inside_candle(df).iloc[1]


class TestBreakouts:
    def test_breakout_up_detected(self):
        rows = flat_bars(25, base=100) + [{"open": 100, "close": 108, "high": 108, "low": 100, "volume": 10}]
        df = make_df(rows)
        assert pa.is_breakout_up(df, lookback=20).iloc[-1]
        assert not pa.is_breakout_down(df, lookback=20).iloc[-1]

    def test_no_breakout_within_range(self):
        rows = flat_bars(25, base=100) + [{"open": 100, "close": 100.5, "high": 101, "low": 100, "volume": 10}]
        df = make_df(rows)
        assert not pa.is_breakout_up(df, lookback=20).iloc[-1]

    def test_failed_breakout_up(self):
        # 25 quiet bars, then a breakout bar, then 2 bars closing back below the broken level.
        rows = flat_bars(25, base=100)
        rows.append({"open": 100, "close": 108, "high": 108, "low": 100, "volume": 10})   # breakout
        rows.append({"open": 107, "close": 103, "high": 107, "low": 102, "volume": 10})   # pulling back
        rows.append({"open": 103, "close": 100.5, "high": 103, "low": 100, "volume": 10})  # failed, back inside
        df = make_df(rows)
        result = pa.is_failed_breakout_up(df, lookback=20, within_bars=3)
        assert result.iloc[-1]
        assert not result.iloc[-3]  # the breakout bar itself isn't a "failed breakout"

    def test_no_failed_breakout_when_breakout_holds(self):
        rows = flat_bars(25, base=100)
        rows.append({"open": 100, "close": 108, "high": 108, "low": 100, "volume": 10})
        rows.append({"open": 108, "close": 110, "high": 111, "low": 107, "volume": 10})
        rows.append({"open": 110, "close": 112, "high": 113, "low": 109, "volume": 10})
        df = make_df(rows)
        assert not pa.is_failed_breakout_up(df, lookback=20, within_bars=3).iloc[-1]


class TestNoLookahead:
    """The core discipline check: every price_action function must give
    identical output on a truncated prefix vs. the full series, for every
    row within that prefix. If truncating the data changes a past value,
    something in the module is peeking into the future."""

    def _synthetic_series(self, n: int = 120) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 20))})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [40, 70, 100])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(120)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = pa.compute_price_action(full)
        truncated_result = pa.compute_price_action(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("pa_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
