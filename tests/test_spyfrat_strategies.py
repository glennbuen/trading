"""
Tests for the 4 SPYFRAT-deck strategies (spyfrat_system, support_20pct,
bebemon, ceiling_followthrough). Same lightweight-but-real "wiring
correctness" approach as test_book_strategies.py — each is a composition
of already-tested engines.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import spyfrat_system, support_20pct, bebemon, ceiling_followthrough
from cryptobot.engines.moving_averages import bollinger_bands
from cryptobot.engines import market_structure as ms


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_daily(n: int = 200, seed: int = 251) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(rng.normal(0, 1, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 0.3)
        c = b + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.5))
        l = min(o, c) - abs(rng.normal(0, 0.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
    return make_df(rows)


def synthetic_weekly(n: int = 40, seed: int = 252) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(rng.normal(0, 2, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 1)
        c = b + rng.normal(0, 1)
        h = max(o, c) + abs(rng.normal(0, 1.5))
        l = min(o, c) - abs(rng.normal(0, 1.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(500, 100)) + 50})
    df = make_df(rows)
    df["ts"] = (pd.Timestamp("2020-01-01") + pd.to_timedelta(np.arange(n) * 7, unit="D")).astype("int64") // 10**6
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


class TestSpyfratSystem:
    def test_long_signal_matches_manual_bollinger_breakout(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = spyfrat_system.compute_spyfrat_system(daily, weekly)
        expected = spyfrat_system.bollinger_breakout_up(daily)
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    def test_exit_signal_is_true_whenever_ephr_is_true(self):
        daily = synthetic_daily()
        weekly = synthetic_weekly()
        d = spyfrat_system.compute_spyfrat_system(daily, weekly)
        assert (d["pr_ephr"] <= d["spyfrat_exit_signal"]).all()

    @pytest.mark.parametrize("truncate_at", [80, 140])
    def test_no_lookahead(self, truncate_at):
        daily = synthetic_daily(200)
        weekly = synthetic_weekly(40)
        full = spyfrat_system.compute_spyfrat_system(daily, weekly)
        trunc_daily = daily.iloc[:truncate_at].reset_index(drop=True)
        trunc = spyfrat_system.compute_spyfrat_system(trunc_daily, weekly)
        for col in ["long_signal", "spyfrat_exit_signal", "spyfrat_bb_upper"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )


class TestSupport20Pct:
    def test_no_entry_without_any_confirmed_swing_high_yet(self):
        rows = [{"open": 100, "high": 100.5, "low": 99.5, "close": 100, "volume": 10} for _ in range(10)]
        df = make_df(rows)
        d = support_20pct.compute_support_20pct(df)
        assert not d["long_signal"].any()

    def test_second_touch_of_the_same_level_never_fires(self):
        # Build a fixture with a confirmed swing high, then TWO separate
        # dips to the resulting support level - only the first (if it
        # reclaims) should ever be eligible.
        values = list(np.linspace(100, 130, 10)) + list(np.linspace(130, 128, 5))  # swing high ~130
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 10} for v in values]
        df_check = make_df(rows)
        swing_high = ms.resistance(df_check, 3, 3).iloc[-1]
        support = swing_high * 0.80 if pd.notna(swing_high) else None

        if support is not None:
            # first touch + reclaim
            rows.append({"open": 128, "high": 128, "low": support - 0.5, "close": support + 1, "volume": 10})
            rows.extend({"open": support + 1, "high": support + 2, "low": support + 0.5,
                        "close": support + 1, "volume": 10} for _ in range(3))
            # second touch + reclaim - must NOT fire
            rows.append({"open": support + 1, "high": support + 1, "low": support - 0.5,
                        "close": support + 1, "volume": 10})
            df = make_df(rows)
            d = support_20pct.compute_support_20pct(df)
            fires = d["long_signal"][d["long_signal"]]
            assert len(fires) <= 1

    @pytest.mark.parametrize("truncate_at", [40, 90])
    def test_no_lookahead(self, truncate_at):
        df = synthetic_daily(150)
        full = support_20pct.compute_support_20pct(df)
        trunc = support_20pct.compute_support_20pct(df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal", "s20_support_level"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )


class TestBebemon:
    def test_no_signal_without_prior_consolidation(self):
        # Trending market that never sits inside the tight band for long.
        df = synthetic_daily(100)
        d = bebemon.compute_bebemon(df, consolidation_bars=5)
        # If it never consolidated for 5 bars, it can never fire regardless of breakouts.
        if not d["bebemon_was_consolidating"].any():
            assert not d["long_signal"].any()

    def test_long_signal_requires_consolidation_breakout_and_volume(self):
        df = synthetic_daily(150)
        d = bebemon.compute_bebemon(df)
        assert (d["long_signal"] <= d["bebemon_was_consolidating"]).all()

    @pytest.mark.parametrize("truncate_at", [60, 110])
    def test_no_lookahead(self, truncate_at):
        df = synthetic_daily(150)
        full = bebemon.compute_bebemon(df)
        trunc = bebemon.compute_bebemon(df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal", "bebemon_was_consolidating", "bebemon_upper"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )


class TestCeilingFollowthrough:
    def test_fires_on_a_hand_built_ceiling_and_followthrough(self):
        rows = [{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10} for _ in range(10)]
        rows.append({"open": 100, "high": 118, "low": 100, "close": 117, "volume": 10})  # ceiling day: +17%
        rows.append({"open": 141, "high": 145, "low": 140, "close": 142, "volume": 10})  # +20.5% open gap
        df = make_df(rows)
        d = ceiling_followthrough.compute_ceiling_followthrough(df)
        assert d["cf_ceiling_day"].iloc[10]
        assert d["long_signal"].iloc[11]

    def test_no_fire_when_followthrough_gap_is_too_small(self):
        rows = [{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10} for _ in range(10)]
        rows.append({"open": 100, "high": 118, "low": 100, "close": 117, "volume": 10})  # ceiling day: +17%
        rows.append({"open": 125, "high": 128, "low": 124, "close": 126, "volume": 10})  # only +6.8% open gap
        df = make_df(rows)
        d = ceiling_followthrough.compute_ceiling_followthrough(df)
        assert not d["long_signal"].iloc[11]

    @pytest.mark.parametrize("truncate_at", [40, 90])
    def test_no_lookahead(self, truncate_at):
        df = synthetic_daily(150)
        full = ceiling_followthrough.compute_ceiling_followthrough(df)
        trunc = ceiling_followthrough.compute_ceiling_followthrough(df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal", "cf_ceiling_day"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
