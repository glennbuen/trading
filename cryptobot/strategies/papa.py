"""
PAPA — "The Forbidden Book" Strategy 4 of 7. Envelope + MACD + ALMA, for
traders who can only check the market once or twice a day.

Book's exact rules (Daily timeframe, Envelope Length=40/Percent=3/
Exponential basis — the book's own explicit settings):
  Buy: MACD line crosses above the zero line AND candle breaks the upper
       envelope line.
  Exit: EITHER 1) MACD line curves down, OR 2) candle breaks ALMA as
        support (an OR of two conditions — implemented via the backtest
        engine's signal_exit method, since this doesn't reduce to a
        single close-vs-one-line comparison the way trailing_indicator
        expects).

"This doesn't work sa mga biglang lipad na basura stocks" (the book's own
note) — PAPA is deliberately less reactive than the others, filtering out
explosive/parabolic moves by requiring the slower zero-line MACD cross.

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.engines.moving_averages import (
    alma, envelope, DEFAULT_ALMA_WINDOW, DEFAULT_ALMA_OFFSET, DEFAULT_ALMA_SIGMA,
    DEFAULT_ENVELOPE_LENGTH, DEFAULT_ENVELOPE_PERCENT,
)
from cryptobot.engines import macd as macd_mod


def envelope_breakout_up(df: pd.DataFrame, length: int = DEFAULT_ENVELOPE_LENGTH,
                          percent: float = DEFAULT_ENVELOPE_PERCENT) -> pd.Series:
    _, upper, _ = envelope(df["close"], length, percent, basis="ema")
    above = df["close"] > upper
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def compute_papa(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                  alma_offset: float = DEFAULT_ALMA_OFFSET, alma_sigma: float = DEFAULT_ALMA_SIGMA,
                  envelope_length: int = DEFAULT_ENVELOPE_LENGTH, envelope_percent: float = DEFAULT_ENVELOPE_PERCENT,
                  macd_fast: int = macd_mod.DEFAULT_FAST, macd_slow: int = macd_mod.DEFAULT_SLOW,
                  macd_signal: int = macd_mod.DEFAULT_SIGNAL) -> pd.DataFrame:
    d = df.copy()
    d["papa_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)
    basis, upper, lower = envelope(d["close"], envelope_length, envelope_percent, basis="ema")
    d["papa_envelope_upper"] = upper

    macd_zero_cross = macd_mod.cross_up_zero(d["close"], macd_fast, macd_slow, macd_signal)
    env_breakout = envelope_breakout_up(d, envelope_length, envelope_percent)
    d["papa_macd_cross_up_zero"] = macd_zero_cross
    d["papa_envelope_breakout"] = env_breakout
    d["long_signal"] = macd_zero_cross & env_breakout

    macd_down = macd_mod.curving_down(d["close"], macd_fast, macd_slow, macd_signal)
    below_alma = d["close"] < d["papa_alma"]
    d["papa_exit_signal"] = macd_down.fillna(False) | below_alma.fillna(False)
    return d
