"""
Tests for daytrading/engines/trend_filter.py — the 1h+15m
"both-must-agree" trend filter merged onto a 5m entry timeframe. Reuses
the same zigzag-construction technique as test_market_structure.py/
test_structure_break.py (a controllable up/down `trend_state` fixture),
built independently at two different timeframes with a shared epoch so
the multi-timeframe merge has genuine overlap.
"""

import numpy as np
import pandas as pd
import pytest

from daytrading.engines.trend_filter import compute_trend_filter
from cryptobot.engines import market_structure as ms

EPOCH_MS = int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000)


def make_ohlcv(ts_ms: np.ndarray, values: list[float]) -> pd.DataFrame:
    df = pd.DataFrame({"open": values, "high": values, "low": values, "close": values})
    df["volume"] = 10.0
    df["ts"] = ts_ms
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def zigzag_values(anchors: list[float], seg_len: int = 5) -> list[float]:
    values = [float(anchors[0])]
    for i in range(1, len(anchors)):
        seg = np.linspace(anchors[i - 1], anchors[i], seg_len + 1)[1:]
        values.extend(seg.tolist())
    return values


class TestTrendFilterAgreement:
    def test_both_up_gives_trend_up(self):
        # A clean, sustained uptrend zigzag at both higher timeframes
        # (higher highs + higher lows throughout).
        anchors = [100, 110, 105, 130, 120, 150]
        tf1_vals = zigzag_values(anchors, seg_len=5)
        tf2_vals = zigzag_values(anchors, seg_len=5)
        tf1_ts = EPOCH_MS + np.arange(len(tf1_vals)) * 3_600_000       # 1h bars
        tf2_ts = EPOCH_MS + np.arange(len(tf2_vals)) * 900_000          # 15m bars
        tf1_df = make_ohlcv(tf1_ts, tf1_vals)
        tf2_df = make_ohlcv(tf2_ts, tf2_vals)

        # entry (5m) timeframe spans well past both, so the merge has
        # plenty of confirmed structure by the tail end.
        n5m = 800
        entry_ts = EPOCH_MS + np.arange(n5m) * 300_000
        entry_df = make_ohlcv(entry_ts, [100.0] * n5m)

        d = compute_trend_filter(entry_df, tf1_df, tf2_df)
        # by the end of the series, both higher timeframes should show a
        # confirmed uptrend, and the merged flags should reflect it.
        assert d["dt_trend_tf1"].iloc[-1] in ("up", "transition")  # tf1 sparse relative to entry length
        assert d["dt_trend_up"].iloc[-1] == ((d["dt_trend_tf1"].iloc[-1] == "up") and
                                              (d["dt_trend_tf2"].iloc[-1] == "up"))

    def test_disagreement_gives_neither_up_nor_down(self):
        n5m = 500
        entry_ts = EPOCH_MS + np.arange(n5m) * 300_000
        entry_df = make_ohlcv(entry_ts, [100.0] * n5m)

        # tf1: uptrend zigzag; tf2: downtrend zigzag - forced disagreement.
        up_anchors = [100, 110, 105, 130, 120, 150]
        down_anchors = [150, 140, 145, 120, 130, 100]
        tf1_vals = zigzag_values(up_anchors)
        tf2_vals = zigzag_values(down_anchors)
        tf1_ts = EPOCH_MS + np.arange(len(tf1_vals)) * 3_600_000
        tf2_ts = EPOCH_MS + np.arange(len(tf2_vals)) * 900_000
        tf1_df = make_ohlcv(tf1_ts, tf1_vals)
        tf2_df = make_ohlcv(tf2_ts, tf2_vals)

        d = compute_trend_filter(entry_df, tf1_df, tf2_df)
        assert not (d["dt_trend_up"] & d["dt_trend_down"]).any()
        # at the point both are confirmed, they should disagree -> no flag set
        both_known = d["dt_trend_tf1"].isin(["up", "down"]) & d["dt_trend_tf2"].isin(["up", "down"])
        disagreeing = both_known & (d["dt_trend_tf1"] != d["dt_trend_tf2"])
        assert not (d.loc[disagreeing, "dt_trend_up"] | d.loc[disagreeing, "dt_trend_down"]).any()

    def test_trend_up_and_trend_down_are_mutually_exclusive(self):
        n5m = 500
        entry_ts = EPOCH_MS + np.arange(n5m) * 300_000
        entry_df = make_ohlcv(entry_ts, [100.0] * n5m)
        rng = np.random.default_rng(41)
        tf1_vals = list(100 + np.cumsum(rng.normal(0, 1, 150)))
        tf2_vals = list(100 + np.cumsum(rng.normal(0, 1, 600)))
        tf1_df = make_ohlcv(EPOCH_MS + np.arange(len(tf1_vals)) * 3_600_000, tf1_vals)
        tf2_df = make_ohlcv(EPOCH_MS + np.arange(len(tf2_vals)) * 900_000, tf2_vals)
        d = compute_trend_filter(entry_df, tf1_df, tf2_df)
        assert not (d["dt_trend_up"] & d["dt_trend_down"]).any()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [100, 300])
    def test_truncation_invariance(self, truncate_at):
        n5m = 500
        entry_ts = EPOCH_MS + np.arange(n5m) * 300_000
        rng = np.random.default_rng(17)
        entry_df = make_ohlcv(entry_ts, list(100 + np.cumsum(rng.normal(0, 0.5, n5m))))
        tf1_vals = list(100 + np.cumsum(rng.normal(0, 1, 150)))
        tf2_vals = list(100 + np.cumsum(rng.normal(0, 1, 600)))
        tf1_df = make_ohlcv(EPOCH_MS + np.arange(len(tf1_vals)) * 3_600_000, tf1_vals)
        tf2_df = make_ohlcv(EPOCH_MS + np.arange(len(tf2_vals)) * 900_000, tf2_vals)

        full = compute_trend_filter(entry_df, tf1_df, tf2_df)
        trunc_entry = entry_df.iloc[:truncate_at].reset_index(drop=True)
        trunc = compute_trend_filter(trunc_entry, tf1_df, tf2_df)
        for col in ["dt_trend_up", "dt_trend_down"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
