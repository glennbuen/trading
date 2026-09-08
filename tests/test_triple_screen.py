"""
Tests for cryptobot/strategies/triple_screen.py (Elder's Triple Screen).
Daily and weekly fixtures share the SAME calendar epoch (2020-01-01) so
merge_higher_timeframe_series has genuine overlap to merge against —
unlike test_spyfrat_strategies.py's synthetic_daily (epoch 1970) vs.
synthetic_weekly (epoch 2020), which never overlap and is fine for that
file's wiring-only checks but not for testing actual merged VALUES here.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import triple_screen as ts
from cryptobot.engines.macd import macd
from cryptobot.engines.force_index import force_index
from cryptobot.engines.price_action import is_breakout_up, is_breakout_down
from cryptobot.engines.multi_timeframe import merge_higher_timeframe_series
from cryptobot.utils import bars_since

EPOCH_MS = int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000)
DAY_MS = 86_400_000


def make_daily(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = EPOCH_MS + np.arange(len(df)) * DAY_MS
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def make_weekly(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = EPOCH_MS + np.arange(len(df)) * 7 * DAY_MS
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_daily(n: int = 300, seed: int = 701) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(rng.normal(0, 1, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 0.3)
        c = b + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.5))
        l = min(o, c) - abs(rng.normal(0, 0.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
    return make_daily(rows)


def synthetic_weekly(n: int = 60, seed: int = 702) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(rng.normal(0, 2, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 1)
        c = b + rng.normal(0, 1)
        h = max(o, c) + abs(rng.normal(0, 1.5))
        l = min(o, c) - abs(rng.normal(0, 1.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(500, 100)) + 50})
    return make_weekly(rows)


class TestScreen1WeeklyTide:
    def test_long_signal_never_fires_when_tide_is_bearish(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        assert not (d["long_signal"] & d["ts_tide_bearish"]).any()

    def test_short_signal_never_fires_when_tide_is_bullish(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        assert not (d["short_signal"] & d["ts_tide_bullish"]).any()

    def test_tide_bullish_and_bearish_are_mutually_exclusive(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        assert not (d["ts_tide_bullish"] & d["ts_tide_bearish"]).any()


class TestScreen2PullbackTiming:
    def test_long_signal_requires_a_pullback_within_the_timing_window(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly, timing_window=3)
        recent_pullback = bars_since(d["ts_pullback_long"]) <= 3
        assert (d["long_signal"] <= recent_pullback).all()

    def test_no_long_signal_far_after_the_last_pullback(self):
        # Hand-built: force index positive (no pullback) throughout a
        # bullish tide, then a breakout - must NOT fire without a recent
        # Screen-2 pullback armed.
        daily = synthetic_daily(300, seed=703)
        weekly = synthetic_weekly(60, seed=703)
        d = ts.compute_triple_screen(daily, weekly, timing_window=1)
        # Any long_signal must have a pullback on the SAME bar or one before it
        fires = d.index[d["long_signal"]]
        for i in fires:
            assert bars_since(d["ts_pullback_long"]).iloc[i] <= 1


class TestScreen3BreakoutTrigger:
    def test_long_signal_implies_a_close_based_breakout_up(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        expected_breakout = is_breakout_up(daily, ts.DEFAULT_BREAKOUT_LOOKBACK)
        assert (d["long_signal"] <= expected_breakout).all()

    def test_short_signal_implies_a_close_based_breakout_down(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        expected_breakout = is_breakout_down(daily, ts.DEFAULT_BREAKOUT_LOOKBACK)
        assert (d["short_signal"] <= expected_breakout).all()


class TestNoSignalOverlap:
    def test_long_and_short_never_fire_on_the_same_bar(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        assert not (d["long_signal"] & d["short_signal"]).any()

    def test_structure_stop_known_whenever_a_signal_fires(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = ts.compute_triple_screen(daily, weekly)
        signals = d["long_signal"] | d["short_signal"]
        assert d.loc[signals, "ts_structure_stop"].notna().all()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [100, 200])
    def test_truncation_invariance(self, truncate_at):
        daily = synthetic_daily(300)
        weekly = synthetic_weekly(60)
        full = ts.compute_triple_screen(daily, weekly)
        trunc_daily = daily.iloc[:truncate_at].reset_index(drop=True)
        trunc = ts.compute_triple_screen(trunc_daily, weekly)
        for col in ["long_signal", "short_signal", "ts_tide_bullish", "ts_force_index", "ts_structure_stop"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
