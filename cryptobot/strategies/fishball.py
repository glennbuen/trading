"""
FISHBALL — "The Forbidden Book" Strategy 2 of 7. Bounce/reversal trade.

Book's exact rules (30-minute timeframe, "non-negotiable" per the book):
  Buy: Fisher was below the extreme oversold "dotted line" recently, then
       crosses back above its trigger, while Trix (length=5, per the
       book) is NOT curving down (flat or rising).
  Exit: Fisher curves down, OR Fisher crosses below its trigger.

"Dotted lines" interpreted as the standard Fisher Transform extreme
reference at +/-1.5 — the book doesn't give an explicit number, and this
is TradingView's default Fisher Transform script convention (same
assumption basis as ALMA's parameters, see moving_averages.py).

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.engines import oscillators as osc

DEFAULT_TRIX_LENGTH = 5  # book's explicit setting for FISHBALL specifically
DEFAULT_EXTREME = 1.5
DEFAULT_EXTREME_LOOKBACK = 10


def compute_fishball(df: pd.DataFrame, fisher_length: int = osc.DEFAULT_FISHER_LENGTH,
                      trix_length: int = DEFAULT_TRIX_LENGTH, extreme: float = DEFAULT_EXTREME,
                      extreme_lookback: int = DEFAULT_EXTREME_LOOKBACK) -> pd.DataFrame:
    d = df.copy()
    fisher, trigger = osc.fisher_transform(d, fisher_length)
    trix = osc.trix(d["close"], trix_length)
    d["fishball_fisher"] = fisher
    d["fishball_trigger"] = trigger
    d["fishball_trix"] = trix

    was_oversold_bool = (fisher.shift(1) <= -extreme).fillna(False)
    was_oversold_recently = was_oversold_bool.rolling(extreme_lookback).max().fillna(0).astype(bool)

    cross_up_trigger = (fisher > trigger) & (fisher.shift(1) <= trigger.shift(1))
    trix_not_falling = (trix >= trix.shift(1)).fillna(False)

    d["fishball_was_oversold"] = was_oversold_recently
    d["long_signal"] = was_oversold_recently & cross_up_trigger.fillna(False) & trix_not_falling

    # Exit: Fisher curves down (was rising, now falling — same pattern as
    # macd.curving_down) OR crosses below its trigger.
    rising = fisher > fisher.shift(1)
    was_rising = rising.shift(1).fillna(False).astype(bool)
    fisher_curving_down = was_rising & ~rising
    cross_down_trigger = (fisher < trigger) & (fisher.shift(1) >= trigger.shift(1))
    d["fishball_exit_signal"] = fisher_curving_down.fillna(False) | cross_down_trigger.fillna(False)
    return d
