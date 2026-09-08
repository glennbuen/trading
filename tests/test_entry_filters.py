import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.entry_filters import near_ema_pullback, compute_entry_filters
from cryptobot.engines.moving_averages import ema


def make_df(closes: list[float]) -> pd.DataFrame:
    df = pd.DataFrame({"open": closes, "high": [c + 0.5 for c in closes],
                        "low": [c - 0.5 for c in closes], "close": closes, "volume": 10.0})
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestNearEmaPullback:
    def test_close_just_below_ema_within_threshold_is_near_long(self):
        # Flat-then-slight-dip series so EMA sits just above the final close.
        closes = [100.0] * 15 + [99.5]
        df = make_df(closes)
        near_long, near_short = near_ema_pullback(df, ema_period=10, max_distance_pct=2.0)
        assert near_long.iloc[-1]
        assert not near_short.iloc[-1]

    def test_close_far_below_ema_is_not_near(self):
        closes = [100.0] * 15 + [90.0]  # a big drop, well outside 2%
        df = make_df(closes)
        near_long, near_short = near_ema_pullback(df, ema_period=10, max_distance_pct=2.0)
        assert not near_long.iloc[-1]
        assert not near_short.iloc[-1]

    def test_close_above_ema_is_never_near_long(self):
        closes = [100.0] * 15 + [100.3]  # close is ABOVE the ema, wrong side for a long pullback
        df = make_df(closes)
        near_long, near_short = near_ema_pullback(df, ema_period=10, max_distance_pct=2.0)
        assert not near_long.iloc[-1]
        assert near_short.iloc[-1]

    def test_long_and_short_are_mutually_exclusive(self):
        rng = np.random.default_rng(21)
        closes = list(100 + np.cumsum(rng.normal(0, 1.5, 100)))
        df = make_df(closes)
        near_long, near_short = near_ema_pullback(df)
        # exactly-at-the-ema bars can count as both "at or below" and "at
        # or above" (a boundary case), but never with a nonzero distance
        both = near_long & near_short
        if both.any():
            e = ema(df["close"], 10)
            assert np.allclose(df.loc[both, "close"], e.loc[both])

    def test_tighter_threshold_finds_fewer_bars(self):
        rng = np.random.default_rng(5)
        closes = list(100 + np.cumsum(rng.normal(0, 1.5, 200)))
        df = make_df(closes)
        loose_long, loose_short = near_ema_pullback(df, max_distance_pct=5.0)
        tight_long, tight_short = near_ema_pullback(df, max_distance_pct=0.5)
        assert tight_long.sum() <= loose_long.sum()
        assert tight_short.sum() <= loose_short.sum()

    def test_compute_entry_filters_attaches_columns(self):
        df = make_df([100.0] * 20)
        d = compute_entry_filters(df)
        assert {"ef_ema", "ef_near_ema_long", "ef_near_ema_short"}.issubset(d.columns)


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [30, 70])
    def test_truncation_invariance(self, truncate_at):
        rng = np.random.default_rng(9)
        closes = list(100 + np.cumsum(rng.normal(0, 1.5, 100)))
        df = make_df(closes)
        full_long, full_short = near_ema_pullback(df)
        trunc_long, trunc_short = near_ema_pullback(df.iloc[:truncate_at].reset_index(drop=True))
        pd.testing.assert_series_equal(
            full_long.iloc[:truncate_at].reset_index(drop=True),
            trunc_long.reset_index(drop=True), check_names=False,
        )
        pd.testing.assert_series_equal(
            full_short.iloc[:truncate_at].reset_index(drop=True),
            trunc_short.reset_index(drop=True), check_names=False,
        )
