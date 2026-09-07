"""
MFI Reversal Strategy — the classic textbook Money Flow Index signal,
tested faithfully on its own terms (like Ichimoku Cross), not augmented
with this project's other engines.

Entry: MFI reclaims the oversold zone from below (long) / loses the
overbought zone from above (short) — the standard oscillator-reversal
signal, not a discretionary embellishment.

Exit: ATR-based stop/target, same framework as most of this project's
other strategies, for direct comparability (unlike Ichimoku Cross, MFI
has no natural structural stop reference of its own).

No lookahead: money_flow_index.py's every component is a plain rolling
sum, backward-looking by construction (see that module's docstring) —
this module adds no new temporal decisions.
"""

import pandas as pd

from cryptobot.engines import money_flow_index as mfi

DEFAULT_PERIOD = mfi.DEFAULT_PERIOD
DEFAULT_OVERSOLD = mfi.DEFAULT_OVERSOLD
DEFAULT_OVERBOUGHT = mfi.DEFAULT_OVERBOUGHT


def compute_mfi_reversal(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                          oversold: int = DEFAULT_OVERSOLD,
                          overbought: int = DEFAULT_OVERBOUGHT) -> pd.DataFrame:
    d = mfi.compute_mfi(df, period, oversold, overbought)
    d["long_signal"] = d["mfi_cross_up_oversold"]
    d["short_signal"] = d["mfi_cross_down_overbought"]
    return d
