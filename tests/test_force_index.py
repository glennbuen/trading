import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.force_index import raw_force_index, force_index, compute_force_index


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="D", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestRawForceIndex:
    def test_positive_on_a_rising_close_with_volume(self):
        df = make_df([
            {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"open": 100, "high": 106, "low": 100, "close": 105, "volume": 20},
        ])
        r = raw_force_index(df)
        assert r.iloc[1] == pytest.approx(20 * (105 - 100))

    def test_negative_on_a_falling_close(self):
        df = make_df([
            {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10},
            {"open": 100, "high": 100, "low": 94, "close": 95, "volume": 15},
        ])
        r = raw_force_index(df)
        assert r.iloc[1] == pytest.approx(15 * (95 - 100))

    def test_nan_on_the_first_bar(self):
        df = make_df([{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10}])
        assert pd.isna(raw_force_index(df).iloc[0])


class TestSmoothedForceIndex:
    def test_smoothing_reduces_noise_vs_the_raw_series(self):
        rng = np.random.default_rng(11)
        n = 100
        rows = []
        for _ in range(n):
            c = 100 + rng.normal(0, 2)
            rows.append({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": abs(rng.normal(100, 50))})
        df = make_df(rows)
        raw = raw_force_index(df)
        smoothed = force_index(df, smoothing=2)
        assert smoothed.dropna().std() <= raw.dropna().std()

    def test_compute_force_index_attaches_column(self):
        df = make_df([{"open": 100, "high": 101, "low": 99, "close": 100, "volume": 10} for _ in range(10)])
        d = compute_force_index(df)
        assert "force_index" in d.columns


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [30, 70])
    def test_truncation_invariance(self, truncate_at):
        rng = np.random.default_rng(3)
        n = 100
        rows = []
        for _ in range(n):
            c = 100 + rng.normal(0, 2)
            rows.append({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": abs(rng.normal(100, 50))})
        df = make_df(rows)
        full = force_index(df)
        trunc = force_index(df.iloc[:truncate_at].reset_index(drop=True))
        pd.testing.assert_series_equal(
            full.iloc[:truncate_at].reset_index(drop=True),
            trunc.reset_index(drop=True), check_names=False,
        )
