"""
Money Flow Index (MFI) Engine — the "volume-weighted RSI."

A genuinely different hypothesis from every strategy tested so far in
this project: RSI-style overbought/oversold oscillation, but weighted by
money flow (typical price × volume) rather than price change alone.
Unlike Ichimoku, MFI has no forward-plotted lookahead trap — every
component here is a plain rolling sum over the trailing `period` bars,
backward-looking by construction like the rest of this project's engines.

Formula, reformulated for numerical robustness (algebraically identical
to the classic textbook version, MFI = 100 - 100/(1 + PositiveFlow/
NegativeFlow)):

    MFI = 100 * PositiveFlow / (PositiveFlow + NegativeFlow)

The reformulation matters for a real edge case the classic ratio-based
formula mishandles: if PositiveFlow > 0 and NegativeFlow == 0, both
formulas correctly give 100 (all money flow was positive). But if BOTH
are zero (typical price never changed at all across the whole window —
rare but not impossible on flat/zero-volume synthetic data), the classic
ratio formula produces NaN → 100 (spuriously "maximally overbought"),
while this formulation cleanly falls through to a neutral 50 via the
explicit `.fillna(50)` guard below — the mathematically honest answer
for "no directional money flow happened at all," not "everything was
bullish."
"""

import numpy as np
import pandas as pd

DEFAULT_PERIOD = 14
DEFAULT_OVERSOLD = 20
DEFAULT_OVERBOUGHT = 80


def typical_price(df: pd.DataFrame) -> pd.Series:
    return (df["high"] + df["low"] + df["close"]) / 3


def raw_money_flow(df: pd.DataFrame) -> pd.Series:
    return typical_price(df) * df["volume"]


def money_flow_index(df: pd.DataFrame, period: int = DEFAULT_PERIOD) -> pd.Series:
    tp = typical_price(df)
    rmf = tp * df["volume"]
    tp_diff = tp.diff()

    positive_flow = rmf.where(tp_diff > 0, 0.0)
    negative_flow = rmf.where(tp_diff < 0, 0.0)
    positive_sum = positive_flow.rolling(period).sum()
    negative_sum = negative_flow.rolling(period).sum()

    total = positive_sum + negative_sum
    return (100 * positive_sum / total.replace(0, np.nan)).fillna(50)


def is_oversold(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                 oversold: int = DEFAULT_OVERSOLD) -> pd.Series:
    return money_flow_index(df, period) < oversold


def is_overbought(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                   overbought: int = DEFAULT_OVERBOUGHT) -> pd.Series:
    return money_flow_index(df, period) > overbought


def cross_up_from_oversold(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                            oversold: int = DEFAULT_OVERSOLD) -> pd.Series:
    """Classic MFI reversal-buy signal: MFI reclaims the oversold zone
    from below (was <= threshold, now > it) — the standard textbook
    entry, not a discretionary embellishment."""
    mfi = money_flow_index(df, period)
    return (mfi > oversold) & (mfi.shift(1) <= oversold)


def cross_down_from_overbought(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                                overbought: int = DEFAULT_OVERBOUGHT) -> pd.Series:
    mfi = money_flow_index(df, period)
    return (mfi < overbought) & (mfi.shift(1) >= overbought)


def compute_mfi(df: pd.DataFrame, period: int = DEFAULT_PERIOD,
                 oversold: int = DEFAULT_OVERSOLD, overbought: int = DEFAULT_OVERBOUGHT) -> pd.DataFrame:
    d = df.copy()
    d["mfi"] = money_flow_index(d, period)
    d["mfi_oversold"] = is_oversold(d, period, oversold)
    d["mfi_overbought"] = is_overbought(d, period, overbought)
    d["mfi_cross_up_oversold"] = cross_up_from_oversold(d, period, oversold)
    d["mfi_cross_down_overbought"] = cross_down_from_overbought(d, period, overbought)
    return d
