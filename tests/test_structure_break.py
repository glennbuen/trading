"""
Tests for cryptobot/engines/structure_break.py — the "valid low / valid
high" market-structure definition from the SWAG... no, the "3-step
formula" YouTube video transcript. Reuses the exact zigzag fixture from
test_market_structure.py (same anchors/timing) so the expected values
here can be hand-derived against already-verified market_structure
output, and specifically targets the video's own key claim: a
`break_of_structure_down` event does NOT flip this engine's trend if the
level broken isn't the true (deeper, previously-validated) valid_low.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import market_structure as ms
from cryptobot.engines import structure_break as sb


def make_flat_df(values: list[float]) -> pd.DataFrame:
    df = pd.DataFrame({"open": values, "high": values, "low": values, "close": values})
    df["volume"] = 10.0
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def zigzag_series() -> pd.DataFrame:
    """Identical construction to test_market_structure.py's zigzag_series:
    start(100) -> peak1(110) -> trough1(95) -> peak2_HH(125) ->
    trough2_HL(102) -> peak3_LH(118) -> trough3_LL(90) -> end(130),
    seg_len=5, so anchor k lands at index k*5 and is confirmed (left=
    right=3) at index k*5+3."""
    anchors = [100, 110, 95, 125, 102, 118, 90, 130]
    seg_len = 5
    values = [float(anchors[0])]
    for i in range(1, len(anchors)):
        seg = np.linspace(anchors[i - 1], anchors[i], seg_len + 1)[1:]
        values.extend(seg.tolist())
    return make_flat_df(values)


class TestValidLowHighAlternation:
    def test_first_valid_low_set_on_breaking_peak1(self):
        # Breaking peak1's confirmed high (110) at idx13 validates
        # trough1's low (95) as the first-ever valid_low.
        df = zigzag_series()
        d = sb.compute_structure_break(df, left=3, right=3)
        assert d["sb_trend"].iloc[13] == "up"
        assert d["sb_valid_low"].iloc[13] == pytest.approx(95.0)

    def test_unvalidated_break_of_structure_down_does_not_flip_trend(self):
        # This is the video's central teaching point. At idx28, price
        # (101.2) closes BELOW market_structure's own trailed-up support
        # level (102) - a real break_of_structure_down by that engine's
        # definition - but 101.2 is still well ABOVE the true, previously
        # validated valid_low (95). This engine must NOT flip to "down"
        # here; market_structure's own bos_down, checked as a control,
        # DOES fire at this exact bar - proving the two are genuinely
        # different definitions, not a redundant reimplementation.
        df = zigzag_series()
        d = sb.compute_structure_break(df, left=3, right=3)
        bos_down = ms.break_of_structure_down(df, left=3, right=3)
        assert bos_down.iloc[28]  # control: market_structure DOES see a break here
        assert d["sb_trend"].iloc[28] == "up"  # this engine correctly does not
        assert d["sb_valid_low"].iloc[28] == pytest.approx(95.0)  # unchanged

    def test_trend_flips_down_only_when_the_true_valid_low_is_broken(self):
        # idx30 (trough3_LL, close=90) is the first bar that actually
        # closes below the standing valid_low (95).
        df = zigzag_series()
        d = sb.compute_structure_break(df, left=3, right=3)
        assert d["sb_trend"].iloc[29] == "up"
        assert d["sb_trend"].iloc[30] == "down"
        assert d["sb_valid_high"].iloc[30] == pytest.approx(118.0)  # the LH that preceded the breakdown

    def test_trend_flips_back_up_and_valid_low_advances_to_a_new_point(self):
        # idx34 breaks back above valid_high (118) -> flips up again, and
        # the new valid_low is transferred to trough3_LL's own low (90),
        # NOT the original 95 - matches the video's "our new low will be
        # transferred from this point to this one" example.
        df = zigzag_series()
        d = sb.compute_structure_break(df, left=3, right=3)
        assert d["sb_trend"].iloc[33] == "down"
        assert d["sb_trend"].iloc[34] == "up"
        assert d["sb_valid_low"].iloc[34] == pytest.approx(90.0)

    def test_undefined_before_any_structure_break(self):
        df = zigzag_series()
        d = sb.compute_structure_break(df, left=3, right=3)
        assert (d["sb_trend"].iloc[:13] == "undefined").all()
        assert d["sb_valid_low"].iloc[:13].isna().all()
        assert d["sb_valid_high"].iloc[:13].isna().all()


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150, seed: int = 331) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        base = 100 + np.cumsum(rng.normal(0, 1.5, n))
        return make_flat_df(base.tolist())

    @pytest.mark.parametrize("truncate_at", [50, 90, 130])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = sb.compute_structure_break(full, left=3, right=3)
        truncated_result = sb.compute_structure_break(truncated, left=3, right=3)

        for col in ["sb_trend", "sb_valid_low", "sb_valid_high", "sb_trend_up", "sb_trend_down"]:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False, obj=col,
            )
