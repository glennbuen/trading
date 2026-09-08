"""
Tests for daytrading/strategies/wrapper.py — build_daytrading_signal_fn.
Uses TITA's compute_tita as the wrapped strategy (already-tested,
simple long-only entry column) to verify wiring: the gated entry column
implies both the original strategy signal AND the trend filter.
"""

import numpy as np
import pandas as pd
import pytest

from daytrading.strategies.wrapper import build_daytrading_signal_fn
from cryptobot.strategies.tita import compute_tita
from cryptobot.strategies.liquidity_sweep_reversal import compute_liquidity_sweep_reversal

EPOCH_MS = int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000)


def make_ohlcv(ts_ms, values, seed=1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for v in values:
        o = v + rng.normal(0, 0.1)
        c = v + rng.normal(0, 0.1)
        h = max(o, c) + abs(rng.normal(0, 0.2))
        l = min(o, c) - abs(rng.normal(0, 0.2))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 30)) + 10})
    df = pd.DataFrame(rows)
    df["ts"] = ts_ms
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_set(n5m=800, seed=201):
    rng = np.random.default_rng(seed)
    base5m = 100 + np.cumsum(rng.normal(0, 0.3, n5m))
    entry_df = make_ohlcv(EPOCH_MS + np.arange(n5m) * 300_000, base5m, seed=seed)

    base1h = 100 + np.cumsum(rng.normal(0, 1, 150))
    tf1_df = make_ohlcv(EPOCH_MS + np.arange(150) * 3_600_000, base1h, seed=seed + 1)

    base15m = 100 + np.cumsum(rng.normal(0, 0.6, 600))
    tf2_df = make_ohlcv(EPOCH_MS + np.arange(600) * 900_000, base15m, seed=seed + 2)
    return entry_df, tf1_df, tf2_df


class TestWrapperWiring:
    def test_gated_long_signal_implies_original_signal_and_trend_up(self):
        entry_df, tf1_df, tf2_df = synthetic_set()
        signal_fn = build_daytrading_signal_fn(compute_tita, "long_signal", None, tf1_df, tf2_df)
        d = signal_fn(entry_df)
        assert (d["long_signal_dt"] <= d["long_signal"]).all()
        assert (d["long_signal_dt"] <= d["dt_trend_up"]).all()

    def test_short_column_defaults_to_false_when_strategy_is_long_only(self):
        entry_df, tf1_df, tf2_df = synthetic_set()
        signal_fn = build_daytrading_signal_fn(compute_tita, "long_signal", None, tf1_df, tf2_df)
        d = signal_fn(entry_df)
        assert not d["short_signal_dt"].any()

    def test_two_sided_strategy_gates_both_sides(self):
        entry_df, tf1_df, tf2_df = synthetic_set(seed=301)
        signal_fn = build_daytrading_signal_fn(compute_liquidity_sweep_reversal, "long_signal", "short_signal",
                                                 tf1_df, tf2_df)
        d = signal_fn(entry_df)
        assert (d["long_signal_dt"] <= d["dt_trend_up"]).all()
        assert (d["short_signal_dt"] <= d["dt_trend_down"]).all()
        assert not (d["long_signal_dt"] & d["short_signal_dt"]).any()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [200, 500])
    def test_truncation_invariance(self, truncate_at):
        entry_df, tf1_df, tf2_df = synthetic_set(n5m=800, seed=401)
        signal_fn = build_daytrading_signal_fn(compute_tita, "long_signal", None, tf1_df, tf2_df)
        full = signal_fn(entry_df)
        trunc = signal_fn(entry_df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal_dt", "dt_trend_up"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
