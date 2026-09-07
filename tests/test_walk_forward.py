import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import make_rolling_windows, run_walk_forward


def make_df(n: int, start="2026-01-01") -> pd.DataFrame:
    rng = np.random.default_rng(42)
    base = 100 + np.cumsum(rng.normal(0, 1, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 0.3)
        c = b + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.5))
        l = min(o, c) - abs(rng.normal(0, 0.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 20)) + 5})
    df = pd.DataFrame(rows)
    df["ts"] = range(n)
    df["dt"] = pd.to_datetime(pd.Timestamp(start) + pd.to_timedelta(df["ts"], unit="h"))
    return df


class TestMakeRollingWindows:
    def test_non_overlapping_windows_cover_the_range(self):
        df = make_df(24 * 30)  # 30 days of hourly data
        windows = make_rolling_windows(df, window_days=10, step_days=10)
        assert len(windows) == 2  # a 3rd window would need 10 more days than available
        assert windows[0][0] == df["dt"].iloc[0]
        assert windows[1][0] == windows[0][0] + pd.Timedelta(days=10)

    def test_overlapping_windows_when_step_smaller_than_window(self):
        # +1 day of buffer: n hourly bars span (n-1) hours, so "20 days"
        # of data falls just short of a clean 20-day boundary otherwise.
        df = make_df(24 * 21)
        windows = make_rolling_windows(df, window_days=10, step_days=5)
        assert len(windows) > 2
        # consecutive windows overlap
        assert windows[1][0] < windows[0][1]

    def test_empty_df_returns_no_windows(self):
        df = make_df(0)
        assert make_rolling_windows(df, 10, 10) == []

    def test_window_shorter_than_available_data_returns_none(self):
        df = make_df(24 * 3)  # 3 days
        assert make_rolling_windows(df, window_days=10, step_days=10) == []


def dummy_signal_fn(df: pd.DataFrame) -> pd.DataFrame:
    """Fires a long signal every 20 bars, deterministic and cheap — the
    walk_forward module doesn't care what strategy produced the column,
    only that it exists."""
    d = compute_volatility(df.copy())
    d["long_signal"] = (d.index % 20 == 0) & (d.index > 15)
    return d


class TestRunWalkForward:
    def test_produces_one_result_per_window(self):
        df = make_df(24 * 41)  # 40 full days hourly, +1 day buffer (see note above)
        windows = run_walk_forward(
            df, dummy_signal_fn, "long_signal", None,
            RiskLimits(cooldown_bars=0), StopTargetConfig(method="atr"),
            window_days=10, step_days=10,
        )
        assert len(windows) == 4
        for w in windows:
            assert w.result is not None
            assert w.num_bars > 0
            assert w.start < w.end

    def test_signal_fn_called_once_on_full_data_not_per_window(self):
        call_count = {"n": 0}

        def counting_signal_fn(df):
            call_count["n"] += 1
            return dummy_signal_fn(df)

        df = make_df(24 * 30)
        run_walk_forward(df, counting_signal_fn, "long_signal", None,
                          RiskLimits(cooldown_bars=0), StopTargetConfig(method="atr"),
                          window_days=10, step_days=10)
        assert call_count["n"] == 1

    def test_windows_too_small_are_skipped(self):
        df = make_df(24 * 25)
        windows = run_walk_forward(
            df, dummy_signal_fn, "long_signal", None,
            RiskLimits(cooldown_bars=0), StopTargetConfig(method="atr"),
            window_days=10, step_days=10,
        )
        # every produced window must have at least MIN_WINDOW_BARS bars
        assert all(w.num_bars >= 10 for w in windows)
