"""
Entry Filters Engine — generic, reusable price-location filters,
composable onto ANY strategy's entry signal via a simple AND. Built for
a "near/within striking distance of EMA(10)" retest requested across
every strategy in this project — confirmed with the user before
building: % distance from close to EMA(N) (not ATR-based), and price
required on the FAVORABLE side (a pullback into value, not mere
proximity in either direction) — for a long, close at or below the EMA
but within the threshold; the mirror for a short.
"""

import pandas as pd

from cryptobot.engines.moving_averages import ema

DEFAULT_EMA_PERIOD = 10
DEFAULT_MAX_DISTANCE_PCT = 2.0


def near_ema_pullback(df: pd.DataFrame, ema_period: int = DEFAULT_EMA_PERIOD,
                       max_distance_pct: float = DEFAULT_MAX_DISTANCE_PCT) -> tuple:
    """Returns (near_long, near_short).
    near_long: close is AT OR BELOW the EMA (a pullback into value, the
      favorable side for a long entry) AND within max_distance_pct of it.
    near_short: the mirror — close at or above the EMA, within
      max_distance_pct."""
    e = ema(df["close"], ema_period)
    dist_pct = (df["close"] - e).abs() / e.replace(0, pd.NA) * 100
    near_long = (df["close"] <= e) & (dist_pct <= max_distance_pct)
    near_short = (df["close"] >= e) & (dist_pct <= max_distance_pct)
    return near_long.fillna(False), near_short.fillna(False)


def compute_entry_filters(df: pd.DataFrame, ema_period: int = DEFAULT_EMA_PERIOD,
                           max_distance_pct: float = DEFAULT_MAX_DISTANCE_PCT) -> pd.DataFrame:
    d = df.copy()
    d["ef_ema"] = ema(d["close"], ema_period)
    d["ef_near_ema_long"], d["ef_near_ema_short"] = near_ema_pullback(d, ema_period, max_distance_pct)
    return d
