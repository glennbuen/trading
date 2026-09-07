import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.metrics import BacktestResult
from cryptobot.backtest.walk_forward import (
    make_rolling_windows, run_walk_forward, WalkForwardWindow,
    chain_equity_curves, chained_max_drawdown_pct,
)


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


def _fake_window(label: str, values: list[float], starting_equity: float = 1000.0,
                  start_hour: int = 0) -> WalkForwardWindow:
    idx = pd.date_range("2026-01-01", periods=len(values), freq="h") + pd.Timedelta(hours=start_hour)
    ec = pd.Series(values, index=idx)
    result = BacktestResult(equity_curve=ec, starting_equity=starting_equity,
                             final_equity=values[-1])
    return WalkForwardWindow(label=label, start=idx[0], end=idx[-1], num_bars=len(values), result=result)


class TestChainedEquityCurve:
    def test_chains_two_windows_into_one_continuous_curve(self):
        # Window 1 ends UP 5% from its own reset start; window 2 then
        # resets to 1000 and drops to 900 before partially recovering —
        # a drawdown that's invisible if you only look at each window's
        # OWN peak (window 2's own peak is 1000, its own worst point 900,
        # a 10% within-window drawdown) but is actually much deeper
        # relative to the TRUE running peak set by window 1's high.
        w1 = _fake_window("w1", [1000, 1100, 1050], starting_equity=1000.0, start_hour=0)
        w2 = _fake_window("w2", [1000, 900, 950], starting_equity=1000.0, start_hour=10)

        chained = chain_equity_curves([w1, w2])
        assert len(chained) == 6
        # Hand-computed expected values (see test docstring/PR notes):
        # 1.0 -> 1.10 -> 1.05 -> 1.05 -> 0.945 -> 0.9975
        expected = [1.0, 1.10, 1.05, 1.05, 0.945, 0.9975]
        for actual, exp in zip(chained.values, expected):
            assert actual == pytest.approx(exp, rel=1e-3)

    def test_chained_drawdown_exceeds_any_single_window_drawdown(self):
        w1 = _fake_window("w1", [1000, 1100, 1050], starting_equity=1000.0, start_hour=0)
        w2 = _fake_window("w2", [1000, 900, 950], starting_equity=1000.0, start_hour=10)

        chained_dd = chained_max_drawdown_pct([w1, w2])
        # w2's OWN drawdown (peak 1000 -> trough 900) is only 10%. But
        # relative to the TRUE running peak (1100, set during w1), the
        # trough of 0.945 (in chained terms) is a much deeper drawdown.
        w2_own_drawdown = 10.0
        assert chained_dd > w2_own_drawdown
        assert chained_dd == pytest.approx((1.10 - 0.945) / 1.10 * 100, rel=1e-3)

    def test_empty_windows_list_returns_empty_curve(self):
        assert chain_equity_curves([]).empty
        assert chained_max_drawdown_pct([]) == 0.0

    def test_single_window_chained_drawdown_matches_its_own(self):
        w1 = _fake_window("w1", [1000, 1100, 950], starting_equity=1000.0)
        chained_dd = chained_max_drawdown_pct([w1])
        assert chained_dd == pytest.approx((1100 - 950) / 1100 * 100, rel=1e-3)
