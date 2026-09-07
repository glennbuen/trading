"""
Tests for cryptobot/strategies/four_hour_range_scalp.py. Hand-built
fixtures directly mirror the video's own worked example (a wick-only
break that must NOT count, followed by a real close-confirmed breakout
and reentry), plus wiring/no-lookahead checks.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies.four_hour_range_scalp import compute_four_hour_range_scalp


def make_5m_df(start_utc: str, rows: list[dict]) -> pd.DataFrame:
    ts = pd.date_range(start_utc, periods=len(rows), freq="5min", tz="UTC")
    df = pd.DataFrame(rows)
    df["dt"] = ts
    df["ts"] = ts.astype("int64") // 10**6
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def bar(price: float, spread: float = 0.2) -> dict:
    return {"open": price, "high": price + spread, "low": price - spread, "close": price, "volume": 10.0}


class TestWorkedExample:
    def _base_rows(self):
        # NY midnight = UTC 04:00 (July, EDT). First-4h window = UTC
        # 04:00-08:00. Range forms 95..105 during that window, then
        # stays flat at 100 afterward (all inside the range) until the
        # test injects the breakout/reentry sequence.
        rows = []
        for i in range(48):  # 4 hours of 5m bars = 48 bars, forming the window
            price = 100 + (5 if i % 6 == 0 else -5 if i % 6 == 3 else 0)
            rows.append(bar(price, spread=0.1))
        rows[0] = bar(105, spread=0.1)   # sets the window high
        rows[24] = bar(95, spread=0.1)   # sets the window low
        # a few flat bars right after the window closes, still inside range
        rows.extend(bar(100, spread=0.1) for _ in range(5))
        return rows

    def test_wick_only_break_does_not_count_as_a_setup(self):
        rows = self._base_rows()
        # a bar whose LOW wicks below range_low(95) but CLOSES back inside
        rows.append({"open": 96, "high": 96.5, "low": 93.0, "close": 96.2, "volume": 10.0})
        rows.extend(bar(100, spread=0.1) for _ in range(3))
        df = make_5m_df("2026-07-01 04:00:00", rows)
        d = compute_four_hour_range_scalp(df)
        assert not d["fhr_breakout_down_event"].any()
        assert not d["long_signal"].any()

    def test_close_confirmed_breakout_down_then_reentry_gives_long_signal(self):
        rows = self._base_rows()
        rows.append({"open": 96, "high": 96.5, "low": 92.0, "close": 93.0, "volume": 10.0})  # real close-below
        rows.append(bar(94, spread=0.1))  # still outside
        rows.append({"open": 94, "high": 96.5, "low": 93.5, "close": 96.0, "volume": 10.0})  # closes back inside
        df = make_5m_df("2026-07-01 04:00:00", rows)
        d = compute_four_hour_range_scalp(df)
        breakout_idx = 48 + 5
        reentry_idx = 48 + 5 + 2
        assert d["fhr_breakout_down_event"].iloc[breakout_idx]
        assert d["long_signal"].iloc[reentry_idx]
        assert not d["short_signal"].iloc[reentry_idx]
        # stop = the lowest low reached during the whole excursion (92.0)
        assert d["fhr_structure_stop"].iloc[reentry_idx] == pytest.approx(92.0)

    def test_close_confirmed_breakout_up_then_reentry_gives_short_signal(self):
        rows = self._base_rows()
        rows.append({"open": 106, "high": 109.0, "low": 105.5, "close": 107.0, "volume": 10.0})
        rows.append(bar(108, spread=0.1))
        rows.append({"open": 108, "high": 108.5, "low": 104.0, "close": 104.5, "volume": 10.0})
        df = make_5m_df("2026-07-01 04:00:00", rows)
        d = compute_four_hour_range_scalp(df)
        reentry_idx = 48 + 5 + 2
        assert d["short_signal"].iloc[reentry_idx]
        assert not d["long_signal"].iloc[reentry_idx]
        assert d["fhr_structure_stop"].iloc[reentry_idx] == pytest.approx(109.0)

    def test_never_reentering_before_day_end_gives_no_signal(self):
        rows = self._base_rows()
        rows.append({"open": 96, "high": 96.5, "low": 92.0, "close": 93.0, "volume": 10.0})
        # stays outside for the rest of the NY day (never closes back inside)
        rows.extend({"open": 93, "high": 93.5, "low": 90, "close": 91, "volume": 10.0} for _ in range(300))
        df = make_5m_df("2026-07-01 04:00:00", rows)
        d = compute_four_hour_range_scalp(df)
        assert not d["long_signal"].any()
        assert not d["short_signal"].any()


class TestWiring:
    def _synthetic_series(self, n: int = 2000, seed: int = 601) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        ts = pd.date_range("2026-07-01 04:00:00", periods=n, freq="5min", tz="UTC")
        base = 100 + np.cumsum(rng.normal(0, 0.3, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.05)
            c = b + rng.normal(0, 0.05)
            h = max(o, c) + abs(rng.normal(0, 0.15))
            l = min(o, c) - abs(rng.normal(0, 0.15))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10.0})
        df = pd.DataFrame(rows)
        df["dt"] = ts
        df["ts"] = ts.astype("int64") // 10**6
        return df[["ts", "dt", "open", "high", "low", "close", "volume"]]

    def test_signals_never_overlap(self):
        df = self._synthetic_series()
        d = compute_four_hour_range_scalp(df)
        assert not (d["long_signal"] & d["short_signal"]).any()

    def test_structure_stop_always_known_at_signal_bars(self):
        df = self._synthetic_series()
        d = compute_four_hour_range_scalp(df)
        signals = d["long_signal"] | d["short_signal"]
        assert d.loc[signals, "fhr_structure_stop"].notna().all()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [500, 1200])
    def test_truncation_invariance(self, truncate_at):
        df = TestWiring()._synthetic_series(2000)
        full = compute_four_hour_range_scalp(df)
        trunc = compute_four_hour_range_scalp(df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal", "short_signal", "fhr_range_high", "fhr_range_low", "fhr_structure_stop"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
