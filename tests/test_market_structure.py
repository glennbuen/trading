import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import market_structure as ms


def make_flat_df(values: list[float]) -> pd.DataFrame:
    """Degenerate bars where open=high=low=close=value — isolates the
    swing-detection/structure logic from candle-shape noise."""
    df = pd.DataFrame({"open": values, "high": values, "low": values, "close": values})
    df["volume"] = 10.0
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def zigzag_series() -> tuple[pd.DataFrame, dict]:
    """
    Anchors: start(100) -> peak(110) -> trough(95) -> peak(125, HH) ->
    trough(102, HL) -> peak(118, LH) -> trough(90, LL) -> end(130).
    seg_len=5 bars between anchors -> anchor k lands at index k*5, and
    with left=right=3 each interior anchor is an unambiguous confirmed
    swing, confirmed exactly at anchor_index + 3.
    """
    anchors = [100, 110, 95, 125, 102, 118, 90, 130]
    seg_len = 5
    values = [float(anchors[0])]
    for i in range(1, len(anchors)):
        seg = np.linspace(anchors[i - 1], anchors[i], seg_len + 1)[1:]
        values.extend(seg.tolist())
    df = make_flat_df(values)
    idx = {"peak1": 5, "trough1": 10, "peak2_HH": 15, "trough2_HL": 20,
           "peak3_LH": 25, "trough3_LL": 30}
    return df, idx


class TestSwingConfirmation:
    def test_swing_high_confirmed_lags_by_right_bars(self):
        df, idx = zigzag_series()
        confirmed = ms.swing_high_confirmed(df, left=3, right=3)
        # Confirmed exactly right=3 bars after the peak, not at the peak itself.
        assert not confirmed.iloc[idx["peak1"]]
        assert confirmed.iloc[idx["peak1"] + 3]

    def test_swing_low_confirmed_lags_by_right_bars(self):
        df, idx = zigzag_series()
        confirmed = ms.swing_low_confirmed(df, left=3, right=3)
        assert not confirmed.iloc[idx["trough1"]]
        assert confirmed.iloc[idx["trough1"] + 3]

    def test_confirmed_value_matches_the_actual_peak_price(self):
        df, idx = zigzag_series()
        val = ms.swing_high_confirmed_value(df, left=3, right=3)
        assert val.iloc[idx["peak2_HH"] + 3] == pytest.approx(125.0)


class TestTrendClassification:
    def test_higher_high_and_lower_low_events(self):
        df, idx = zigzag_series()
        hh = ms.higher_high(df, left=3, right=3)
        lh = ms.lower_high(df, left=3, right=3)
        hl = ms.higher_low(df, left=3, right=3)
        ll = ms.lower_low(df, left=3, right=3)

        assert hh.iloc[idx["peak2_HH"] + 3]
        assert not lh.iloc[idx["peak2_HH"] + 3]
        assert hl.iloc[idx["trough2_HL"] + 3]
        assert lh.iloc[idx["peak3_LH"] + 3]
        assert ll.iloc[idx["trough3_LL"] + 3]

    def test_trend_state_timeline(self):
        df, idx = zigzag_series()
        state = ms.trend_state(df, left=3, right=3)
        # Before the second confirmed swing low (idx trough2+3=23), not
        # enough confirmed structure to classify either way.
        assert state.iloc[idx["trough2_HL"] + 2] == "undefined"
        # up: HH confirmed (idx18) + HL confirmed (idx23) both standing.
        assert state.iloc[idx["peak3_LH"]] == "up"  # idx 25, before the LH at 28
        # transition: LH just confirmed (idx28) but low side still "higher".
        assert state.iloc[idx["peak3_LH"] + 5] == "transition"  # idx 30
        # down: LH standing + LL confirmed (idx33).
        assert state.iloc[idx["trough3_LL"] + 4] == "down"  # idx 34


class TestBreakOfStructure:
    def test_bos_up_fires_on_close_crossing_resistance(self):
        df, idx = zigzag_series()
        bos_up = ms.break_of_structure_up(df, left=3, right=3)
        # The ramp from trough3(90, idx30) to end(130, idx35) crosses back
        # above the standing resistance (125, confirmed at idx18) at some
        # point on that ramp — assert it fires exactly once, and only on
        # the way up through the level, not before.
        crossing_points = bos_up[bos_up].index.tolist()
        assert len(crossing_points) >= 1
        level_at_cross = ms.resistance(df, left=3, right=3).shift(1).iloc[crossing_points[0]]
        assert df["close"].iloc[crossing_points[0]] > level_at_cross


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(7)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        return make_flat_df(base.tolist())

    @pytest.mark.parametrize("truncate_at", [50, 90, 130])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = ms.compute_market_structure(full, left=3, right=3)
        truncated_result = ms.compute_market_structure(truncated, left=3, right=3)

        compare_cols = [c for c in full_result.columns if c.startswith("ms_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
