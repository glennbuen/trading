"""
MACD (Moving Average Convergence Divergence).

Built for "The Forbidden Book" strategy set (MAMA and PAPA both use MACD
with default settings — 12/26/9, per the book's own formula section).
Plain EMA differences, backward-looking by construction.
"""

import pandas as pd

from cryptobot.engines.moving_averages import ema

DEFAULT_FAST = 12
DEFAULT_SLOW = 26
DEFAULT_SIGNAL = 9


def macd(series: pd.Series, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
          signal: int = DEFAULT_SIGNAL) -> tuple:
    """Returns (macd_line, signal_line, histogram)."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def cross_up(series: pd.Series, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
             signal: int = DEFAULT_SIGNAL) -> pd.Series:
    macd_line, signal_line, _ = macd(series, fast, slow, signal)
    bull = macd_line > signal_line
    was_bull = bull.shift(1).fillna(False).astype(bool)  # see ichimoku.py's docstring on why this cast matters
    return bull & ~was_bull


def cross_down(series: pd.Series, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
                signal: int = DEFAULT_SIGNAL) -> pd.Series:
    macd_line, signal_line, _ = macd(series, fast, slow, signal)
    bear = macd_line < signal_line
    was_bear = bear.shift(1).fillna(False).astype(bool)
    return bear & ~was_bear


def cross_up_zero(series: pd.Series, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
                   signal: int = DEFAULT_SIGNAL) -> pd.Series:
    """PAPA's specific trigger: the MACD LINE crossing above zero (not
    the signal-line cross MAMA uses)."""
    macd_line, _, _ = macd(series, fast, slow, signal)
    above = macd_line > 0
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def curving_down(series: pd.Series, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
                  signal: int = DEFAULT_SIGNAL) -> pd.Series:
    """PAPA's exit condition: "MACD line nagcurve pababa" (the MACD line
    turns downward) — its slope goes from rising to falling."""
    macd_line, _, _ = macd(series, fast, slow, signal)
    rising = macd_line > macd_line.shift(1)
    was_rising = rising.shift(1).fillna(False).astype(bool)
    return was_rising & ~rising


def compute_macd(df: pd.DataFrame, fast: int = DEFAULT_FAST, slow: int = DEFAULT_SLOW,
                  signal: int = DEFAULT_SIGNAL) -> pd.DataFrame:
    d = df.copy()
    d["macd_line"], d["macd_signal"], d["macd_hist"] = macd(d["close"], fast, slow, signal)
    d["macd_cross_up"] = cross_up(d["close"], fast, slow, signal)
    d["macd_cross_down"] = cross_down(d["close"], fast, slow, signal)
    d["macd_cross_up_zero"] = cross_up_zero(d["close"], fast, slow, signal)
    d["macd_curving_down"] = curving_down(d["close"], fast, slow, signal)
    return d
