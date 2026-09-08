"""
Day-Trading Strategy Wrapper — adapts each of this project's existing
swing/position strategies' distinctive entry-trigger logic into a day-
trading version. Confirmed with the user before building: rebuild ALL
14 strategies with a real entry signal (from `scripts/
retest_all_with_exit_rules.py`'s set), each one's own entry logic
recomputed on a 5m timeframe (this package's "5 minutes for entry"
design) and gated by the 1h+15m trend filter (`engines/trend_filter.py`)
instead of whatever daily/weekly trend context the original strategy
used — a genuinely different context for a genuinely different holding-
period discipline, not a cosmetic change.

Reuses each strategy's own `compute_*` function UNCHANGED — 5m OHLCV is
a well-formed input to every one of them (none require the daily
timeframe specifically; their engines are all timeframe-agnostic,
parameterized by bar counts, not calendar time), so the only new logic
here is the trend-filter gate.

`build_daytrading_signal_fn` closes over the two higher-timeframe
dataframes (full history, never windowed) rather than accepting them as
separate `run_walk_forward` arguments, because `run_walk_forward`'s own
contract is `signal_fn(df) -> df` — computed ONCE on the full entry-
timeframe history, then WINDOWED. The higher timeframes must stay full-
history for that one computation (the merge itself is already no-
lookahead-safe by construction — market_structure.trend_state() and
merge_higher_timeframe_series are both independently tested for this —
so running the merge once on full history before windowing the OUTPUT
is the same established-safe pattern this project uses for every
strategy's own signal_fn, not a new risk).
"""

import pandas as pd

from cryptobot.engines.volatility import compute_volatility
from daytrading.engines.trend_filter import compute_trend_filter


def build_daytrading_signal_fn(compute_fn, long_col: str, short_col: str | None,
                                tf1_df: pd.DataFrame, tf2_df: pd.DataFrame, **kwargs):
    """Returns a signal_fn(entry_df_5m) -> df, matching run_walk_forward's
    expected shape, with long_signal_dt/short_signal_dt as the gated
    entry columns."""
    def signal_fn(entry_df_5m: pd.DataFrame) -> pd.DataFrame:
        d = compute_volatility(entry_df_5m.copy())
        d = compute_fn(d, **kwargs)
        d = compute_trend_filter(d, tf1_df, tf2_df)
        d["long_signal_dt"] = d[long_col].fillna(False) & d["dt_trend_up"]
        d["short_signal_dt"] = (d[short_col].fillna(False) & d["dt_trend_down"]) if short_col else False
        return d
    return signal_fn
