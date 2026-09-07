"""
TITA — "The Forbidden Book" Strategy 5 of 7. RSI + ALMA.

Book's exact rules (Daily timeframe, RSI configured with "upper limit=55,
lower limit=50" — narrow bands around the midline, read here as momentum-
territory markers rather than classic 30/70 overbought/oversold):
  Buy: EITHER 1) RSI crosses up through 50, OR 2) RSI >= 55 AND candle
       breaks ALMA as resistance (simultaneous breakout).
  Exit: candle breaks below ALMA and stays below (trailing_indicator).

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.engines.moving_averages import (
    alma, DEFAULT_ALMA_WINDOW, DEFAULT_ALMA_OFFSET, DEFAULT_ALMA_SIGMA,
)
from cryptobot.engines.oscillators import rsi, DEFAULT_RSI_LENGTH

DEFAULT_RSI_LOWER = 50
DEFAULT_RSI_UPPER = 55


def alma_breakout_up(df: pd.DataFrame, window: int = DEFAULT_ALMA_WINDOW,
                      offset: float = DEFAULT_ALMA_OFFSET, sigma: float = DEFAULT_ALMA_SIGMA) -> pd.Series:
    a = alma(df["close"], window, offset, sigma)
    above = df["close"] > a
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def compute_tita(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                  alma_offset: float = DEFAULT_ALMA_OFFSET, alma_sigma: float = DEFAULT_ALMA_SIGMA,
                  rsi_length: int = DEFAULT_RSI_LENGTH, rsi_lower: float = DEFAULT_RSI_LOWER,
                  rsi_upper: float = DEFAULT_RSI_UPPER) -> pd.DataFrame:
    d = df.copy()
    d["tita_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)
    r = rsi(d["close"], rsi_length)
    d["tita_rsi"] = r

    cond1 = (r > rsi_lower) & (r.shift(1) <= rsi_lower)
    breakout = alma_breakout_up(d, alma_window, alma_offset, alma_sigma)
    cond2 = (r >= rsi_upper) & breakout
    d["tita_rsi_cross_50"] = cond1.fillna(False)
    d["tita_rsi55_and_breakout"] = cond2
    d["long_signal"] = cond1.fillna(False) | cond2
    return d
