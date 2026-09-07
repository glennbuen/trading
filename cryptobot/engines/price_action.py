"""
Price Action Engine — objective, deterministic candle-shape detection.

Every function here operates on a canonical OHLCV DataFrame and returns a
pandas Series aligned to it. NOTHING in this module assumes a pattern is
profitable — these are descriptive primitives for strategies to combine
and backtest, not signals in themselves (per the architecture brief: "Do
not assume a candlestick pattern is profitable. Every pattern must be
testable.").

No-lookahead discipline: every rolling/average calculation that a value is
compared against uses ONLY prior bars (`.shift(1)` before `.rolling(...)`),
never the current bar's own value in its own baseline, and never any bar
after the one being evaluated. This is verified directly in
tests/test_price_action.py via a truncation-invariance check: computing a
column on the full dataset vs. a truncated prefix must produce identical
values on the overlapping rows. If that test fails, there's a lookahead
bug — it's not a style preference.
"""

import numpy as np
import pandas as pd

from cryptobot.utils import bars_since

DEFAULT_LOOKBACK = 20
DEFAULT_BODY_FRAC = 0.6
DEFAULT_WICK_FRAC = 0.6
DEFAULT_REL_SIZE = 1.0
DEFAULT_FAILED_BREAKOUT_WINDOW = 3


def candle_body(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["open"]).abs()


def candle_range(df: pd.DataFrame) -> pd.Series:
    return df["high"] - df["low"]


def upper_wick(df: pd.DataFrame) -> pd.Series:
    return df["high"] - df[["open", "close"]].max(axis=1)


def lower_wick(df: pd.DataFrame) -> pd.Series:
    return df[["open", "close"]].min(axis=1) - df["low"]


def body_fraction(df: pd.DataFrame) -> pd.Series:
    """Body as a fraction of the full candle range. 0 when range is 0
    (a doji on a completely flat bar) rather than NaN/inf."""
    rng = candle_range(df)
    return (candle_body(df) / rng.replace(0, np.nan)).fillna(0)


def relative_candle_size(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    """Current bar's range vs. the average range of the PRECEDING
    `lookback` bars (current bar excluded from its own baseline)."""
    rng = candle_range(df)
    baseline = rng.shift(1).rolling(lookback).mean()
    return rng / baseline.replace(0, np.nan)


def is_strong_bullish(df: pd.DataFrame, body_frac: float = DEFAULT_BODY_FRAC,
                       min_rel_size: float = DEFAULT_REL_SIZE,
                       lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    return ((df["close"] > df["open"]) &
            (body_fraction(df) >= body_frac) &
            (relative_candle_size(df, lookback) >= min_rel_size).fillna(False))


def is_strong_bearish(df: pd.DataFrame, body_frac: float = DEFAULT_BODY_FRAC,
                       min_rel_size: float = DEFAULT_REL_SIZE,
                       lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    return ((df["close"] < df["open"]) &
            (body_fraction(df) >= body_frac) &
            (relative_candle_size(df, lookback) >= min_rel_size).fillna(False))


def is_bullish_rejection(df: pd.DataFrame, wick_frac: float = DEFAULT_WICK_FRAC) -> pd.Series:
    """Long lower wick dominating the range: sellers pushed price down,
    buyers rejected it before the close. Direction-neutral on open/close
    (the wick is the signal, not the body color)."""
    rng = candle_range(df).replace(0, np.nan)
    return (lower_wick(df) / rng >= wick_frac).fillna(False)


def is_bearish_rejection(df: pd.DataFrame, wick_frac: float = DEFAULT_WICK_FRAC) -> pd.Series:
    """Long upper wick dominating the range: buyers pushed price up,
    sellers rejected it before the close."""
    rng = candle_range(df).replace(0, np.nan)
    return (upper_wick(df) / rng >= wick_frac).fillna(False)


def is_inside_candle(df: pd.DataFrame) -> pd.Series:
    """Current bar's range is fully contained within the prior bar's
    range — consolidation/indecision. Uses only the prior bar."""
    return (df["high"] <= df["high"].shift(1)) & (df["low"] >= df["low"].shift(1))


def breakout_level_up(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    """The high being broken for an upside breakout: the max high of the
    PRECEDING `lookback` bars (current bar excluded)."""
    return df["high"].shift(1).rolling(lookback).max()


def breakout_level_down(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    return df["low"].shift(1).rolling(lookback).min()


def is_breakout_up(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    return (df["close"] > breakout_level_up(df, lookback)).fillna(False)


def is_breakout_down(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    return (df["close"] < breakout_level_down(df, lookback)).fillna(False)


def is_failed_breakout_up(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                           within_bars: int = DEFAULT_FAILED_BREAKOUT_WINDOW) -> pd.Series:
    """
    An upside breakout occurred within the last `within_bars` bars, and
    the current close has now dropped back below the level that was
    broken — the breakout failed to hold. Every input here (the breakout
    flag, the level, "bars since") is computed strictly from bar <= i, so
    this is safe to evaluate live on the bar it fires, not just in
    hindsight.
    """
    level = breakout_level_up(df, lookback)
    broke = is_breakout_up(df, lookback)
    # Forward-fill the level from the most recent breakout bar — this only
    # ever propagates a PAST value into the present, never a future one.
    level_of_last_breakout = level.where(broke).ffill()
    since_breakout = bars_since(broke)
    return ((since_breakout > 0) & (since_breakout <= within_bars) &
            (df["close"] < level_of_last_breakout)).fillna(False)


def is_failed_breakout_down(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                             within_bars: int = DEFAULT_FAILED_BREAKOUT_WINDOW) -> pd.Series:
    level = breakout_level_down(df, lookback)
    broke = is_breakout_down(df, lookback)
    level_of_last_breakdown = level.where(broke).ffill()
    since_breakdown = bars_since(broke)
    return ((since_breakdown > 0) & (since_breakdown <= within_bars) &
            (df["close"] > level_of_last_breakdown)).fillna(False)


def compute_price_action(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                          body_frac: float = DEFAULT_BODY_FRAC,
                          wick_frac: float = DEFAULT_WICK_FRAC,
                          min_rel_size: float = DEFAULT_REL_SIZE,
                          failed_breakout_window: int = DEFAULT_FAILED_BREAKOUT_WINDOW) -> pd.DataFrame:
    """Convenience: compute every price-action column at once and return
    df with them attached. Individual functions remain independently
    callable/testable above."""
    d = df.copy()
    d["pa_body"] = candle_body(d)
    d["pa_range"] = candle_range(d)
    d["pa_upper_wick"] = upper_wick(d)
    d["pa_lower_wick"] = lower_wick(d)
    d["pa_body_frac"] = body_fraction(d)
    d["pa_relative_size"] = relative_candle_size(d, lookback)
    d["pa_strong_bullish"] = is_strong_bullish(d, body_frac, min_rel_size, lookback)
    d["pa_strong_bearish"] = is_strong_bearish(d, body_frac, min_rel_size, lookback)
    d["pa_bullish_rejection"] = is_bullish_rejection(d, wick_frac)
    d["pa_bearish_rejection"] = is_bearish_rejection(d, wick_frac)
    d["pa_inside_candle"] = is_inside_candle(d)
    d["pa_breakout_up"] = is_breakout_up(d, lookback)
    d["pa_breakout_down"] = is_breakout_down(d, lookback)
    d["pa_failed_breakout_up"] = is_failed_breakout_up(d, lookback, failed_breakout_window)
    d["pa_failed_breakout_down"] = is_failed_breakout_down(d, lookback, failed_breakout_window)
    return d
