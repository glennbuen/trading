import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import volume as vol


def make_df(volumes: list[float]) -> pd.DataFrame:
    n = len(volumes)
    df = pd.DataFrame({
        "open": [100.0] * n, "high": [101.0] * n, "low": [99.0] * n, "close": [100.0] * n,
        "volume": volumes,
    })
    df["ts"] = range(n)
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestRelativeVolume:
    def test_baseline_excludes_current_bar(self):
        # 20 bars of volume=100, then one bar of volume=1000 (10x the baseline).
        volumes = [100.0] * 20 + [1000.0]
        df = make_df(volumes)
        baseline = vol.volume_baseline(df, lookback=20)
        # Baseline at the spike bar must be ~100 (the prior 20 bars),
        # NOT inflated by including the spike itself.
        assert baseline.iloc[-1] == pytest.approx(100.0)
        rel = vol.relative_volume(df, lookback=20)
        assert rel.iloc[-1] == pytest.approx(10.0)

    def test_spike_detected_above_threshold(self):
        volumes = [100.0] * 20 + [250.0]
        df = make_df(volumes)
        assert vol.is_volume_spike(df, lookback=20, threshold=2.0).iloc[-1]
        assert not vol.is_volume_spike(df, lookback=20, threshold=3.0).iloc[-1]

    def test_expansion_is_a_looser_threshold_than_spike(self):
        volumes = [100.0] * 20 + [130.0]  # 1.3x -> expansion (>=1.2) but not spike (>=2.0)
        df = make_df(volumes)
        assert vol.is_volume_expansion(df, lookback=20, threshold=1.2).iloc[-1]
        assert not vol.is_volume_spike(df, lookback=20, threshold=2.0).iloc[-1]

    def test_contraction_detected_below_threshold(self):
        volumes = [100.0] * 20 + [50.0]  # 0.5x
        df = make_df(volumes)
        assert vol.is_volume_contraction(df, lookback=20, threshold=0.7).iloc[-1]
        assert not vol.is_volume_expansion(df, lookback=20, threshold=1.2).iloc[-1]

    def test_anomaly_flags_either_extreme(self):
        spike = make_df([100.0] * 20 + [300.0])
        quiet = make_df([100.0] * 20 + [30.0])
        normal = make_df([100.0] * 20 + [105.0])
        assert vol.is_volume_anomaly(spike, lookback=20).iloc[-1]
        assert vol.is_volume_anomaly(quiet, lookback=20).iloc[-1]
        assert not vol.is_volume_anomaly(normal, lookback=20).iloc[-1]

    def test_zero_baseline_does_not_crash(self):
        volumes = [0.0] * 20 + [50.0]
        df = make_df(volumes)
        rel = vol.relative_volume(df, lookback=20)
        assert pd.isna(rel.iloc[-1])  # division by zero baseline -> NaN, not inf/crash
        assert not vol.is_volume_spike(df, lookback=20).iloc[-1]  # NaN comparisons -> False, not a crash


class TestVolumeTrend:
    def test_rising_when_recent_average_above_long_average(self):
        volumes = [50.0] * 20 + [200.0] * 5
        df = make_df(volumes)
        assert vol.volume_rising(df, short=5, long=20).iloc[-1]
        assert not vol.volume_falling(df, short=5, long=20).iloc[-1]


class TestNoLookahead:
    def _synthetic_series(self, n: int = 120) -> pd.DataFrame:
        rng = np.random.default_rng(11)
        volumes = np.abs(rng.normal(100, 40, n)) + 10
        return make_df(volumes.tolist())

    @pytest.mark.parametrize("truncate_at", [30, 60, 100])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(120)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = vol.compute_volume(full)
        truncated_result = vol.compute_volume(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("vol_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
