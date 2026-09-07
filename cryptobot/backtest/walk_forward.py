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
from cryptobot.backtest.metrics import BacktestResult
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
