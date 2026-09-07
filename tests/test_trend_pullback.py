import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import trend_pullback as tp


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


STRUCTURE_KWARGS = dict(structure_left=3, structure_right=3, volume_lookback=20,
                         expansion_threshold=1.2, contraction_threshold=0.7)


def bullish_base_rows() -> list[dict]:
    """Establishes an 'up' trend_state by idx23 (short zigzag [100,110,95,
    125,102] ending idx20, then a gentle rise through idx25 to let the
    idx20 swing low confirm) — verified interactively before writing this
    fixture, same technique as test_market_structure.py's zigzag."""
    values = zigzag_from_anchors([100, 110, 95, 125, 102], seg_len=5)
    rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
    for i in range(1, 6):
        v = 102 + i * 1.2
        rows.append({"open": v, "high": v + 0.5, "low": v - 0.5, "close": v, "volume": 50.0})
    return rows  # idx0-25, trend_state == "up" from idx23


def bullish_fixture(pullback_low: float = 112.0, pullback_volume: float = 20.0,
                     continuation_close: float = 120.0, continuation_volume: float = 200.0) -> pd.DataFrame:
    rows = bullish_base_rows()
    rows.append({"open": 108, "high": 119, "low": 107, "close": 118, "volume": 60.0})   # idx26 impulse
    rows.append({"open": 118, "high": 118, "low": pullback_low, "close": 114, "volume": pullback_volume})  # idx27 pullback
    # continuation candle deliberately NOT "strong" (body_frac < 0.6) so it
    # doesn't re-trigger a fresh impulse/episode on the same bar it's
    # meant to confirm — see module docstring / ARCHITECTURE.md note.
    rows.append({"open": 116, "high": 123, "low": 112, "close": continuation_close,
                 "volume": continuation_volume})  # idx28 continuation
    return make_df(rows)


class TestBullishTrendPullback:
    def test_full_sequence_fires_entry_on_continuation_bar(self):
        df = bullish_fixture()
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert result["impulse_event"].iloc[26]
        assert result["entry_signal"].iloc[28]
        assert not result["entry_signal"].iloc[26:28].any()

    def test_no_entry_when_pullback_breaks_structure(self):
        # Pullback low (95) drops well below the support level (~102).
        df = bullish_fixture(pullback_low=95.0)
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert not result["structure_preserved"].iloc[27:].any()
        assert not result["entry_signal"].any()

    def test_no_entry_without_a_volume_contraction_pullback(self):
        # Pullback volume stays high — no "healthy, low-conviction" dip ever occurs.
        df = bullish_fixture(pullback_volume=55.0)
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert not result["contraction_seen"].iloc[27]
        assert not result["entry_signal"].any()

    def test_no_entry_without_continuation_volume_expansion(self):
        df = bullish_fixture(continuation_volume=52.0)  # barely above baseline
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert not result["entry_signal"].any()

    def test_no_entry_without_continuation_beyond_prior_high(self):
        df = bullish_fixture(continuation_close=110.0)  # doesn't clear the impulse's high (119)
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert not result["entry_signal"].any()

    def test_no_impulse_without_an_established_uptrend(self):
        # A strong bullish candle with no prior confirmed uptrend at all.
        rows = [{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 50.0} for _ in range(20)]
        rows.append({"open": 100, "high": 112, "low": 99, "close": 110, "volume": 60.0})
        df = make_df(rows)
        result = tp.scan_trend_pullback_bullish(df, **STRUCTURE_KWARGS)
        assert not result["impulse_event"].any()


def bearish_base_rows() -> list[dict]:
    """Reuses the exact 8-anchor zigzag from test_market_structure.py
    (already proven there to reach a confirmed 'down' trend_state by
    idx33), rather than hand-deriving a new one — the first attempt at a
    fresh 4-anchor zigzag here never actually reached 'down' (caught by
    this file's own sanity assertion before it could masquerade as a
    strategy bug).

    Appends a short tail of small-but-nonzero-range bars: the raw zigzag
    is perfectly flat (open=high=low=close), giving a ZERO relative-
    candle-size baseline — which silently makes is_strong_bullish/bearish
    permanently False on whatever candle comes next (caught by a second,
    separate assertion failure before being mistaken for a strategy bug)."""
    values = zigzag_from_anchors([100, 110, 95, 125, 102, 118, 90, 130], seg_len=5)
    rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]  # idx0-35
    for _ in range(6):
        rows.append({"open": 130, "high": 130.5, "low": 129.5, "close": 130, "volume": 50.0})
    return rows  # idx0-41


class TestBearishTrendPullback:
    def test_mirrored_sequence_fires_entry(self):
        rows = bearish_base_rows()
        df_check = make_df(rows)
        from cryptobot.engines import market_structure as ms
        trend = ms.trend_state(df_check, 3, 3)
        assert trend.iloc[-1] == "down", f"fixture setup didn't reach a down trend: {trend.iloc[-5:].tolist()}"
        assert ms.resistance(df_check, 3, 3).iloc[-1] == pytest.approx(118.0)

        rows.append({"open": 115, "high": 116, "low": 100, "close": 102, "volume": 60.0})  # idx42 impulse down (high stays < resistance=118)
        rows.append({"open": 102, "high": 112, "low": 100, "close": 108, "volume": 20.0})  # idx43 pullback (low vol, stays < 118)
        rows.append({"open": 106, "high": 109, "low": 90, "close": 95, "volume": 200.0})   # idx44 continuation (not "strong")
        df = make_df(rows)
        from cryptobot.engines import price_action as pa
        assert not pa.is_strong_bearish(df).iloc[-1]  # sanity: continuation isn't itself "strong"

        result = tp.scan_trend_pullback_bearish(df, **STRUCTURE_KWARGS)
        assert result["impulse_event"].iloc[42]
        assert result["entry_signal"].iloc[44]
        assert not result["entry_signal"].iloc[42:44].any()


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(53)
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

        full_result = tp.compute_trend_pullback(full, **STRUCTURE_KWARGS)
        truncated_result = tp.compute_trend_pullback(truncated, **STRUCTURE_KWARGS)

        compare_cols = [c for c in full_result.columns if c.startswith("tp_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
