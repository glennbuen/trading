"""
MAMA (MACD + ALMA) — "The Forbidden Book" Strategy 1 of 7.

Book's exact rules (Daily timeframe):
  Buy: 1) candle breaks above ALMA AND 2) MACD bullish cross, allowing the
       cross to land a day before, exactly on, or a day after the ALMA
       breakout (the book's own three stated timing variants: "a day
       before cross, just crossed, 1 day after cross").
  Exit: candle breaks below ALMA and stays below (implemented via the
        backtest engine's trailing_indicator method — see
        cryptobot/backtest/engine.py).

Long-only, matching the book's content — every one of its 7 strategies
describes only buy-then-sell-to-exit setups, never a short/sell-short
trigger, consistent with a Philippine retail-stock-market context where
short-selling isn't generally accessible to retail traders.
"""

import pandas as pd

from cryptobot.utils import bars_since
from cryptobot.engines.moving_averages import (
    alma, DEFAULT_ALMA_WINDOW, DEFAULT_ALMA_OFFSET, DEFAULT_ALMA_SIGMA,
)
from cryptobot.engines import macd as macd_mod

DEFAULT_TIMING_WINDOW = 1  # "a day before, just crossed, or a day after"


def alma_breakout_up(df: pd.DataFrame, window: int = DEFAULT_ALMA_WINDOW,
                      offset: float = DEFAULT_ALMA_OFFSET, sigma: float = DEFAULT_ALMA_SIGMA) -> pd.Series:
    a = alma(df["close"], window, offset, sigma)
    above = df["close"] > a
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def compute_mama(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                  alma_offset: float = DEFAULT_ALMA_OFFSET, alma_sigma: float = DEFAULT_ALMA_SIGMA,
                  macd_fast: int = macd_mod.DEFAULT_FAST, macd_slow: int = macd_mod.DEFAULT_SLOW,
                  macd_signal: int = macd_mod.DEFAULT_SIGNAL,
                  timing_window: int = DEFAULT_TIMING_WINDOW) -> pd.DataFrame:
    d = df.copy()
    d["mama_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)

    breakout = alma_breakout_up(d, alma_window, alma_offset, alma_sigma)
    macd_up = macd_mod.cross_up(d["close"], macd_fast, macd_slow, macd_signal)
    d["mama_alma_breakout"] = breakout
    d["mama_macd_cross_up"] = macd_up

    since_breakout = bars_since(breakout)
    since_macd = bars_since(macd_up)
    # Fires on whichever event happens LATER, once both have occurred
    # within `timing_window` bars of each other — matches all 3 of the
    # book's stated timing variants without hardcoding which event leads.
    d["long_signal"] = (since_breakout <= timing_window) & (since_macd <= timing_window)
    return d
