"""
backtest/walk_forward.py — rolling windows over a backtest, per
architecture spec §25-26: never optimize against (or judge from) the
entire dataset in one shot. Split into windows, roll forward, and look
for a strategy that survives consistently across them rather than one
flattering full-history backtest.

Windowing + result aggregation only — this module doesn't know about any
specific strategy. The caller supplies a `signal_fn(df) -> df` (a
strategy's compute_* function) and the same run_backtest() config used
everywhere else in this package.
"""

from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd

from cryptobot.backtest.engine import run_backtest, BacktestCosts, StopTargetConfig
from cryptobot.backtest.metrics import BacktestResult, max_drawdown_pct_from_curve
from cryptobot.risk.risk_manager import RiskLimits

MIN_WINDOW_BARS = 10


@dataclass
class WalkForwardWindow:
    label: str
    start: pd.Timestamp
    end: pd.Timestamp
    num_bars: int
    result: BacktestResult


def make_rolling_windows(df: pd.DataFrame, window_days: int,
                          step_days: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """(start, end) timestamp pairs covering df's date range. step_days
    == window_days gives non-overlapping windows; step_days < window_days
    gives overlapping ones. Pure windowing — no data slicing here, so
    it's testable without any OHLCV data at all."""
    if df.empty:
        return []
    start_ts = df["dt"].iloc[0]
    end_ts = df["dt"].iloc[-1]
    windows = []
    cursor = start_ts
    while cursor + pd.Timedelta(days=window_days) <= end_ts:
        windows.append((cursor, cursor + pd.Timedelta(days=window_days)))
        cursor += pd.Timedelta(days=step_days)
    return windows


def run_walk_forward(df: pd.DataFrame, signal_fn: Callable[[pd.DataFrame], pd.DataFrame],
                      long_entry_col: str, short_entry_col: Optional[str],
                      risk_limits: RiskLimits, stop_target: StopTargetConfig,
                      window_days: int, step_days: int, costs: BacktestCosts = None,
                      starting_equity: float = 1000.0) -> list[WalkForwardWindow]:
    """
    Runs signal_fn on the FULL df exactly once, then backtests each
    window as an independent slice of the resulting signal dataframe —
    deliberately NOT re-running signal_fn separately per window. Doing
    that would reset every engine's warmup at each window boundary (e.g.
    market_structure needs real prior history before a confirmed swing
    means anything), understating how much history a live system would
    actually have accumulated by that point in time. Note this does NOT
    introduce lookahead: each engine's own no-lookahead guarantee already
    ensures a value at bar i only depends on bars <= i, regardless of
    where a later window boundary happens to fall.
    """
    windows = make_rolling_windows(df, window_days, step_days)
    signals_df = signal_fn(df)

    results = []
    for start, end in windows:
        mask = (signals_df["dt"] >= start) & (signals_df["dt"] < end)
        window_df = signals_df.loc[mask].reset_index(drop=True)
        if len(window_df) < MIN_WINDOW_BARS:
            continue
        result = run_backtest(window_df, long_entry_col, short_entry_col,
                               risk_limits, stop_target, costs, starting_equity)
        results.append(WalkForwardWindow(
            label=f"{start.date()} -> {end.date()}", start=start, end=end,
            num_bars=len(window_df), result=result,
        ))
    return results


def chain_equity_curves(windows: list[WalkForwardWindow]) -> pd.Series:
    """
    Concatenates each window's equity curve into ONE continuous curve, so
    a genuine cumulative (not per-window) drawdown can be reported.

    Each window's `run_backtest` call correctly resets to the same
    `starting_equity` independently — that's the whole point of §25's
    walk-forward design: every window is an unbiased forward test against
    fixed parameters, not distorted by whatever happened to the equity in
    a prior, unrelated window. But that same independence means
    `w.result.max_drawdown_pct` only ever reports the worst drawdown
    *within* one window, understating what a trader who ran this strategy
    continuously through the whole period would actually have
    experienced — documented as a known limitation after Phase 6's
    evaluation of Breakout+Retest (docs/EVALUATION_BREAKOUT_RETEST.md).

    This function reconciles the two: each window's equity curve is
    converted to per-bar RETURNS relative to its own reset starting
    point, then those returns are compounded sequentially onto a single
    running total starting at 1.0. Position sizing during the actual
    walk-forward run is unaffected (it already used each window's own
    reset equity, as intended) — this only changes how the RESULTS are
    stitched together for reporting.
    """
    chained_values = [1.0]
    chained_index = []
    for w in windows:
        ec = w.result.equity_curve
        if ec.empty:
            continue
        returns = ec.pct_change()
        returns.iloc[0] = (ec.iloc[0] - w.result.starting_equity) / w.result.starting_equity
        for dt, r in returns.items():
            r = 0.0 if pd.isna(r) else r
            chained_values.append(chained_values[-1] * (1 + r))
            chained_index.append(dt)
    if not chained_index:
        return pd.Series(dtype=float)
    return pd.Series(chained_values[1:], index=pd.DatetimeIndex(chained_index))


def chained_max_drawdown_pct(windows: list[WalkForwardWindow]) -> float:
    """Cumulative max drawdown across all windows chained together —
    the honest answer to "what was the worst peak-to-trough a continuous
    trader would have seen", vs. any single window's own smaller number."""
    curve = chain_equity_curves(windows)
    return max_drawdown_pct_from_curve(curve)
