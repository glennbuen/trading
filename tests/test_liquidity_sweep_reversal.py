import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import liquidity_sweep_reversal as lsr
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


STRUCTURE_KWARGS = dict(structure_left=3, structure_right=3, max_bars_to_reclaim=3,
                         volume_lookback=20, volume_threshold=1.2)


def down_trend_base_rows() -> list[dict]:
    """Reuses the proven 8-anchor zigzag (confirmed 'down' trend by
    idx33, support=90/resistance=118 by the end), plus a small non-flat
    tail so the relative-volume/candle baselines downstream are
    meaningful — same pattern validated in test_trend_pullback.py."""
    values = zigzag_from_anchors([100, 110, 95, 125, 102, 118, 90, 130], seg_len=5)
    rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
    for _ in range(6):
        rows.append({"open": 130, "high": 130.5, "low": 129.5, "close": 130, "volume": 50.0})
    return rows  # idx0-41, trend_state == "down", support == 90.0


class TestBullishSweepReversal:
    def test_fires_on_sweep_and_reclaim_with_volume(self):
        rows = down_trend_base_rows()
        rows.append({"open": 100, "high": 101, "low": 85, "close": 95, "volume": 200.0})
        df = make_df(rows)
        result = lsr.compute_liquidity_sweep_reversal(df, **STRUCTURE_KWARGS)
        assert result["long_signal"].iloc[-1]
        assert not result["short_signal"].iloc[-1]

    def test_no_signal_without_volume_confirmation(self):
        rows = down_trend_base_rows()
        rows.append({"open": 100, "high": 101, "low": 85, "close": 95, "volume": 52.0})
        df = make_df(rows)
        result = lsr.compute_liquidity_sweep_reversal(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]

    def test_no_signal_without_a_reclaim(self):
        # Sweeps below support but closes back below it too — no reclaim.
        rows = down_trend_base_rows()
        rows.append({"open": 92, "high": 93, "low": 85, "close": 87, "volume": 200.0})
        df = make_df(rows)
        result = lsr.compute_liquidity_sweep_reversal(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]

    def test_no_signal_when_already_in_an_uptrend(self):
        # Same sweep+reclaim+volume shape, but built on an established
        # 'up' trend context instead — Strategy D is specifically a
        # REVERSAL setup (spec: "market-structure shift"), not a dip-buy
        # within an existing uptrend (that's Strategy C's job).
        up_values = zigzag_from_anchors([100, 110, 95, 125, 102], seg_len=5)
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in up_values]
        for i in range(1, 6):
            v = 102 + i * 1.2
            rows.append({"open": v, "high": v + 0.5, "low": v - 0.5, "close": v, "volume": 50.0})
        df_check = make_df(rows)
        assert ms.trend_state(df_check, 3, 3).iloc[-1] == "up"
        support_level = ms.support(df_check, 3, 3).iloc[-1]

        rows.append({"open": support_level + 5, "high": support_level + 6,
                     "low": support_level - 5, "close": support_level + 3, "volume": 200.0})
        df = make_df(rows)
        result = lsr.compute_liquidity_sweep_reversal(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]


class TestBearishSweepReversal:
    def test_fires_on_sweep_and_reclaim_with_volume(self):
        # Mirror: an established 'up' trend, resistance swept and rejected.
        up_values = zigzag_from_anchors([100, 110, 95, 125, 102], seg_len=5)
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in up_values]
        for i in range(1, 6):
            v = 102 + i * 1.2
            rows.append({"open": v, "high": v + 0.5, "low": v - 0.5, "close": v, "volume": 50.0})
        df_check = make_df(rows)
        assert ms.trend_state(df_check, 3, 3).iloc[-1] == "up"
        resistance_level = ms.resistance(df_check, 3, 3).iloc[-1]

        rows.append({"open": resistance_level - 5, "high": resistance_level + 8,
                     "low": resistance_level - 6, "close": resistance_level - 3, "volume": 200.0})
        df = make_df(rows)
        result = lsr.compute_liquidity_sweep_reversal(df, **STRUCTURE_KWARGS)
        assert result["short_signal"].iloc[-1]
        assert not result["long_signal"].iloc[-1]


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(61)
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

        full_result = lsr.compute_liquidity_sweep_reversal(full, **STRUCTURE_KWARGS)
        truncated_result = lsr.compute_liquidity_sweep_reversal(truncated, **STRUCTURE_KWARGS)

        compare_cols = [c for c in full_result.columns if c.startswith("lsr_") or c.endswith("_signal")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
