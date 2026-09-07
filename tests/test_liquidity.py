import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import liquidity as liq
from cryptobot.engines import market_structure as ms


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def zigzag_from_anchors(anchors: list[float], seg_len: int = 5) -> list[float]:
    values = [float(anchors[0])]
    for i in range(1, len(anchors)):
        seg = np.linspace(anchors[i - 1], anchors[i], seg_len + 1)[1:]
        values.extend(seg.tolist())
    return values


def flat_rows_from_values(values: list[float]) -> list[dict]:
    return [{"open": v, "high": v, "low": v, "close": v, "volume": 10} for v in values]


class TestEqualLevels:
    def test_equal_highs_within_tolerance(self):
        # peak1=120 (idx5), trough (idx10), peak2=121 (idx15) -> 0.83% apart, within 5% tolerance.
        values = zigzag_from_anchors([100, 120, 90, 121, 95, 100], seg_len=5)
        df = make_df(flat_rows_from_values(values))
        result = liq.equal_highs(df, left=3, right=3, tolerance_pct=0.05)
        assert result.iloc[15 + 3]  # confirmation bar of the second peak

    def test_not_equal_highs_when_far_apart(self):
        # peak1=110 (idx5), peak2=125 (idx15) -> 13.6% apart, well outside 5% tolerance.
        values = zigzag_from_anchors([100, 110, 95, 125, 102, 118, 90, 130], seg_len=5)
        df = make_df(flat_rows_from_values(values))
        result = liq.equal_highs(df, left=3, right=3, tolerance_pct=0.05)
        assert not result.iloc[15 + 3]

    def test_equal_lows_within_tolerance(self):
        # trough1=95 (idx10), peak (idx15), trough2=95.5 (idx20) -> 0.53% apart.
        values = zigzag_from_anchors([100, 120, 95, 118, 95.5, 122], seg_len=5)
        df = make_df(flat_rows_from_values(values))
        result = liq.equal_lows(df, left=3, right=3, tolerance_pct=0.05)
        assert result.iloc[20 + 3]


class TestRangeLevels:
    def test_range_high_matches_prior_n_bar_max(self):
        values = [100.0] * 10 + [90.0, 95.0, 92.0]
        df = make_df(flat_rows_from_values(values))
        rh = liq.range_high(df, lookback=10)
        # At the last bar, range_high should be the max of the PRECEDING
        # 10 bars, which are all 100 except the two just-appended ones —
        # confirm it doesn't include the current/self bar.
        assert rh.iloc[-1] == pytest.approx(100.0)


def sweep_fixture(reclaim_close: float, extra_flat_bars: int = 3):
    """Establishes a confirmed swing low at 95 (idx5, confirmed idx8),
    then a run of flat bars at 108, then one bar that dips intrabar below
    95 (low=90) with a configurable close, to test reclaim vs. no-reclaim."""
    values = zigzag_from_anchors([100, 95, 108], seg_len=5)  # trough(95) at idx5, confirmed idx8
    rows = flat_rows_from_values(values)
    rows.extend(flat_rows_from_values([108.0] * extra_flat_bars))
    sweep_idx = len(rows)
    rows.append({"open": 100, "high": 101, "low": 90, "close": reclaim_close, "volume": 10})
    return make_df(rows), sweep_idx


class TestLiquiditySweepReversal:
    def test_bullish_sweep_and_same_bar_reclaim(self):
        df, sweep_idx = sweep_fixture(reclaim_close=97)  # closes back above the 95 support
        result = liq.liquidity_sweep_reversal_bullish(df, left=3, right=3, max_bars=3)
        assert result.iloc[sweep_idx]

    def test_bullish_sweep_without_reclaim_does_not_fire(self):
        df, sweep_idx = sweep_fixture(reclaim_close=93)  # stays below the 95 support
        result = liq.liquidity_sweep_reversal_bullish(df, left=3, right=3, max_bars=3)
        assert not result.iloc[sweep_idx]

    def test_reclaim_within_window_after_the_sweep_bar_fires(self):
        df, sweep_idx = sweep_fixture(reclaim_close=93)  # sweep bar itself doesn't reclaim
        df = pd.concat([df, make_df([
            {"open": 93, "high": 94, "low": 92, "close": 94, "volume": 10},
            {"open": 94, "high": 98, "low": 93, "close": 97, "volume": 10},  # reclaims 2 bars later
        ]).drop(columns=["ts", "dt"]).assign(ts=range(len(df), len(df) + 2))], ignore_index=True)
        df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
        result = liq.liquidity_sweep_reversal_bullish(df, left=3, right=3, max_bars=3)
        assert result.iloc[sweep_idx + 2]
        assert not result.iloc[sweep_idx]  # not yet reclaimed on the sweep bar itself

    def test_reclaim_outside_window_does_not_fire(self):
        df, sweep_idx = sweep_fixture(reclaim_close=93)
        extra = make_df([{"open": 93, "high": 94, "low": 92, "close": 93, "volume": 10}] * 3 +
                         [{"open": 93, "high": 98, "low": 93, "close": 97, "volume": 10}])
        extra = extra.drop(columns=["ts", "dt"]).assign(ts=range(len(df), len(df) + 4))
        extra["dt"] = pd.to_datetime(extra["ts"], unit="h", utc=True)
        df = pd.concat([df, extra], ignore_index=True)
        result = liq.liquidity_sweep_reversal_bullish(df, left=3, right=3, max_bars=3)
        assert not result.iloc[sweep_idx + 4]  # reclaim came 4 bars after the sweep, window is 3


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(23)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 20))})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [50, 90, 130])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = liq.compute_liquidity(full, left=3, right=3)
        truncated_result = liq.compute_liquidity(truncated, left=3, right=3)

        compare_cols = [c for c in full_result.columns if c.startswith("liq_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
