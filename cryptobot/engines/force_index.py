"""
Force Index — Alexander Elder's own indicator ("Trading for a Living"),
combining price change and volume into one momentum reading: raw Force
Index = volume x (close - previous close), smoothed with an EMA to
filter noise. Built for `strategies/triple_screen.py`'s Screen 2 (the
intermediate-timeframe oscillator that times pullback entries against
the longer-term trend) — Elder's own stated preference for Triple
Screen specifically uses a short (2-period) EMA smoothing, distinct
from the longer (13-period) smoothing he uses elsewhere for Force Index
divergence analysis, a different technique not built here.
"""

import pandas as pd

from cryptobot.engines.moving_averages import ema

DEFAULT_SMOOTHING = 2


def raw_force_index(df: pd.DataFrame) -> pd.Series:
    return df["volume"] * (df["close"] - df["close"].shift(1))


def force_index(df: pd.DataFrame, smoothing: int = DEFAULT_SMOOTHING) -> pd.Series:
    return ema(raw_force_index(df), smoothing)


def compute_force_index(df: pd.DataFrame, smoothing: int = DEFAULT_SMOOTHING) -> pd.DataFrame:
    d = df.copy()
    d["force_index"] = force_index(d, smoothing)
    return d
