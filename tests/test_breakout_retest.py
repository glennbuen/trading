import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import breakout_retest as br


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


STRUCTURE_KWARGS = dict(structure_left=3, structure_right=3, volume_lookback=5,
                         volume_threshold=1.2, retest_window=5, retest_tolerance_pct=0.01)


def bullish_fixture(retest_close: float = 112.0, include_retest_dip: bool = True) -> pd.DataFrame:
    """
    idx0-10: zigzag [100, 110, 95] establishes a confirmed swing high
    (resistance=110, confirmed at idx8).
    idx11-12: quiet padding at 95, volume=50 (baseline history).
    idx13: BREAKOUT — closes at 115 (>110) on volume=300 (vs ~50 baseline).
    idx14: continues to a local high of 119, volume=60 (unremarkable).
    idx15: RETEST — low dips to 109 (near 110), closes at `retest_close`.
    idx16: CONFIRMATION — closes at 120 (> the 119 post-breakout high),
           volume=250 (expansion again) -> entry_signal should fire here.
    """
    values = zigzag_from_anchors([100, 110, 95], seg_len=5)
    rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
    rows.append({"open": 95, "high": 96, "low": 94, "close": 95, "volume": 50.0})   # idx11
    rows.append({"open": 95, "high": 96, "low": 94, "close": 95, "volume": 50.0})   # idx12
    rows.append({"open": 100, "high": 116, "low": 99, "close": 115, "volume": 300.0})  # idx13 breakout
    rows.append({"open": 116, "high": 119, "low": 115, "close": 118, "volume": 60.0})  # idx14
    if include_retest_dip:
        rows.append({"open": 116, "high": 117, "low": 109, "close": retest_close, "volume": 40.0})  # idx15 retest
        rows.append({"open": 118, "high": 121, "low": 111, "close": 120.0, "volume": 250.0})  # idx16 confirmation
    else:
        # Keeps running without ever coming back near the 110 level again —
        # low stays well clear of 110*(1+tolerance) at every subsequent bar.
        rows.append({"open": 118, "high": 122, "low": 117, "close": 121, "volume": 40.0})   # idx15
        rows.append({"open": 121, "high": 126, "low": 120, "close": 125.0, "volume": 250.0})  # idx16
    return make_df(rows)


class TestBullishBreakoutRetest:
    def test_full_sequence_fires_entry_on_confirmation_bar(self):
        df = bullish_fixture(retest_close=112.0)
        result = br.scan_breakout_retest_bullish(df, **STRUCTURE_KWARGS)
        assert result["breakout_event"].iloc[13]
        assert result["retest_touch"].iloc[15]
        assert result["entry_signal"].iloc[16]
        # Entry must not fire before the confirmation bar.
        assert not result["entry_signal"].iloc[13:16].any()

    def test_entry_fires_only_once_per_episode(self):
        df = bullish_fixture(retest_close=112.0)
        # Append more bars making new highs with volume expansion — should
        # NOT re-fire entry_signal a second time for the same episode.
        extra = make_df([
            {"open": 120, "high": 125, "low": 119, "close": 124, "volume": 200.0},
            {"open": 124, "high": 128, "low": 122, "close": 127, "volume": 200.0},
        ])
        extra = extra.drop(columns=["ts", "dt"])
        extra["ts"] = range(len(df), len(df) + len(extra))
        extra["dt"] = pd.to_datetime(extra["ts"], unit="h", utc=True)
        df2 = pd.concat([df, extra], ignore_index=True)
        result = br.scan_breakout_retest_bullish(df2, **STRUCTURE_KWARGS)
        assert result["entry_signal"].sum() == 1
        assert result["entry_signal"].iloc[16]

    def test_no_entry_when_retest_fails_to_hold(self):
        # Retest bar closes BELOW the level instead of holding above it.
        df = bullish_fixture(retest_close=105.0)
        result = br.scan_breakout_retest_bullish(df, **STRUCTURE_KWARGS)
        assert not result["retest_touch"].iloc[15]
        assert not result["entry_signal"].any()

    def test_no_entry_when_price_never_retests(self):
        # Breaks out and keeps running without ever pulling back to the level.
        df = bullish_fixture(include_retest_dip=False)
        result = br.scan_breakout_retest_bullish(df, **STRUCTURE_KWARGS)
        assert result["breakout_event"].iloc[13]
        assert not result["retested_in_episode"].any()
        assert not result["entry_signal"].any()

    def test_no_entry_without_a_breakout_at_all(self):
        values = zigzag_from_anchors([100, 110, 95, 105, 98], seg_len=5)
        df = make_df([{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values])
        result = br.scan_breakout_retest_bullish(df, **STRUCTURE_KWARGS)
        assert not result["breakout_event"].any()
        assert not result["entry_signal"].any()


class TestBearishBreakoutRetest:
    def test_mirrored_sequence_fires_entry(self):
        # Mirror image of the bullish fixture: support broken to the downside.
        values = zigzag_from_anchors([100, 90, 105], seg_len=5)  # swing low=90 at idx5, confirmed idx8
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
        rows.append({"open": 105, "high": 106, "low": 104, "close": 105, "volume": 50.0})
        rows.append({"open": 105, "high": 106, "low": 104, "close": 105, "volume": 50.0})
        rows.append({"open": 100, "high": 101, "low": 84, "close": 85, "volume": 300.0})   # breakdown
        rows.append({"open": 84, "high": 85, "low": 81, "close": 82, "volume": 60.0})
        rows.append({"open": 84, "high": 91, "low": 83, "close": 88, "volume": 40.0})       # retest of 90
        rows.append({"open": 82, "high": 89, "low": 79, "close": 80.0, "volume": 250.0})    # confirmation
        df = make_df(rows)
        result = br.scan_breakout_retest_bearish(df, **STRUCTURE_KWARGS)
        assert result["breakout_event"].iloc[13]
        assert result["retest_touch"].iloc[15]
        assert result["entry_signal"].iloc[16]


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(31)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [60, 100, 140])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = br.compute_breakout_retest(full, **STRUCTURE_KWARGS)
        truncated_result = br.compute_breakout_retest(truncated, **STRUCTURE_KWARGS)

        compare_cols = [c for c in full_result.columns if c.startswith("br_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
