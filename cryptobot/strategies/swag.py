"""
SWAG Trading System — Jared Odulio (Philippine retail-stock YouTube
content, per the user's own description of a video watched 2026-09-06).
The third source this project has tested that originates from a
Philippine retail-stock trading channel/deck (after "The Forbidden Book"
and the SPYFRAT/Investagrams deck).

User's own description of the 4 components (verbatim, reproduced here so
every design choice below can be checked against it):
  1. Parabolic SAR - spot the trend (uptrend / downtrend).
  2. EMA 13 - "Trigger" - buy if EMA13 is about to cross SMA20 "from
     under".
  3. SMA 20 - "Base" - sell if EMA13 is about to cross SMA20 "from
     above".
  4. MFI - spot whether money is flowing out (downward) or flowing in
     (upward); also used to read oversold/overbought.

This description names 4 well-defined, already-engineered components
(parabolic_sar.py, moving_averages.py's ema/sma, money_flow_index.py) and
is considerably more numeric than either Bebemon or Ceiling/Follow-
Through were — no caveat about the whole strategy being non-numeric is
needed here. Two specific choices ARE this module's own operationalization
of gaps in the description, stated explicitly:

  - "About to cross" is read as the cross EVENT itself (EMA13 crosses
    SMA20), not a predictive "approaching but hasn't yet" signal — this
    project's no-lookahead discipline requires signals to be about
    something that has already happened by the bar's close, not a
    forecast of an imminent cross that might not complete.
  - "Money flowing in/out" (the entry-confirmation half of MFI's stated
    role) is read as the simplest literal midline reading: MFI > 50 =
    net inflow ("flowing in/upward"), MFI < 50 = net outflow. The
    oversold/overbought half of MFI's stated role is wired as the EXIT
    condition instead, reusing money_flow_index.py's existing
    `cross_down_from_overbought` (MFI rolling back down through 80) —
    the same standard MFI reversal-sell trigger already used by this
    project's separate `mfi_reversal.py` strategy, not a new invention.

Long-only (see mama.py's module docstring for why every "Forbidden
Book"/deck-sourced strategy in this project has been long-only).

Exit: EMA13 crosses back below SMA20 (the user's own stated "sell"
trigger) OR the Parabolic SAR trend flips down (the trend filter
reversing invalidates the whole setup) OR MFI rolls back down through
overbought (the stated overbought-exit use of MFI). Composed via
`signal_exit`, same mechanism as SPYFRAT's ePHR/lower-band exit and
FISHBALL's curl-down exit elsewhere in this project.
"""

import pandas as pd

from cryptobot.engines.parabolic_sar import dots_below_price, dots_above_price, DEFAULT_STEP, DEFAULT_MAX_AF
from cryptobot.engines.moving_averages import ema, sma
from cryptobot.engines.money_flow_index import money_flow_index, cross_down_from_overbought, DEFAULT_OVERBOUGHT

DEFAULT_EMA_LENGTH = 13
DEFAULT_SMA_LENGTH = 20
DEFAULT_MFI_LENGTH = 14
DEFAULT_MFI_MIDLINE = 50


def ema_cross_up_sma(df: pd.DataFrame, ema_length: int = DEFAULT_EMA_LENGTH,
                      sma_length: int = DEFAULT_SMA_LENGTH) -> pd.Series:
    fast = ema(df["close"], ema_length)
    slow = sma(df["close"], sma_length)
    above = fast > slow
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def ema_cross_down_sma(df: pd.DataFrame, ema_length: int = DEFAULT_EMA_LENGTH,
                        sma_length: int = DEFAULT_SMA_LENGTH) -> pd.Series:
    fast = ema(df["close"], ema_length)
    slow = sma(df["close"], sma_length)
    below = fast < slow
    was_below = below.shift(1).fillna(False).astype(bool)
    return below & ~was_below


def compute_swag(df: pd.DataFrame, ema_length: int = DEFAULT_EMA_LENGTH,
                  sma_length: int = DEFAULT_SMA_LENGTH, mfi_length: int = DEFAULT_MFI_LENGTH,
                  mfi_midline: float = DEFAULT_MFI_MIDLINE, mfi_overbought: float = DEFAULT_OVERBOUGHT,
                  sar_step: float = DEFAULT_STEP, sar_max_af: float = DEFAULT_MAX_AF) -> pd.DataFrame:
    d = df.copy()

    d["swag_ema"] = ema(d["close"], ema_length)
    d["swag_sma"] = sma(d["close"], sma_length)
    d["swag_trend_up"] = dots_below_price(d, sar_step, sar_max_af)
    trend_down = dots_above_price(d, sar_step, sar_max_af)
    d["swag_mfi"] = money_flow_index(d, mfi_length)

    cross_up = ema_cross_up_sma(d, ema_length, sma_length)
    cross_down = ema_cross_down_sma(d, ema_length, sma_length)
    money_flowing_in = d["swag_mfi"] > mfi_midline
    mfi_exit = cross_down_from_overbought(d, mfi_length, mfi_overbought)

    d["swag_cross_up"] = cross_up
    d["swag_cross_down"] = cross_down
    d["long_signal"] = (
        d["swag_trend_up"].fillna(False) & cross_up.fillna(False) & money_flowing_in.fillna(False)
    )

    trend_flip_down = d["swag_trend_up"].shift(1).fillna(False).astype(bool) & trend_down.fillna(False)
    d["swag_exit_signal"] = cross_down.fillna(False) | trend_flip_down | mfi_exit.fillna(False)
    return d
