"""
Parabolic SAR (Stop and Reverse).

Built for BOPIS ("Parabolic SAR dots below the candle" as a bullish
condition). A genuinely iterative indicator — each bar's SAR value and
trend depend on the previous bar's SAR/trend/extreme-point state, the
same reason SuperTrend needed an explicit loop in this project's earlier
standalone bots (and Fisher Transform needed one in oscillators.py).
Still fully backward-looking: bar i only ever uses state carried forward
from bars < i, never a later bar.

Standard algorithm (Wilder's original), TradingView default parameters
(step=0.02, max=0.2) since the book doesn't specify non-default values
for this indicator.
"""

import numpy as np
import pandas as pd

DEFAULT_STEP = 0.02
DEFAULT_MAX_AF = 0.2


def parabolic_sar(df: pd.DataFrame, step: float = DEFAULT_STEP,
                   max_af: float = DEFAULT_MAX_AF) -> tuple:
    """Returns (sar, trend) where trend is 1 (up, dots below price) or
    -1 (down, dots above price)."""
    high = df["high"].values
    low = df["low"].values
    n = len(df)

    sar = np.full(n, np.nan)
    trend = np.zeros(n, dtype=int)
    if n == 0:
        return pd.Series(sar, index=df.index), pd.Series(trend, index=df.index)

    trend[0] = 1
    sar[0] = low[0]
    ep = high[0]
    af = step

    for i in range(1, n):
        prev_sar = sar[i - 1]
        prior_low = low[i - 2] if i >= 2 else low[i - 1]
        prior_high = high[i - 2] if i >= 2 else high[i - 1]

        if trend[i - 1] == 1:
            candidate = prev_sar + af * (ep - prev_sar)
            candidate = min(candidate, low[i - 1], prior_low)
            if low[i] < candidate:
                trend[i] = -1
                sar[i] = ep
                ep = low[i]
                af = step
            else:
                trend[i] = 1
                sar[i] = candidate
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + step, max_af)
        else:
            candidate = prev_sar + af * (ep - prev_sar)
            candidate = max(candidate, high[i - 1], prior_high)
            if high[i] > candidate:
                trend[i] = 1
                sar[i] = ep
                ep = high[i]
                af = step
            else:
                trend[i] = -1
                sar[i] = candidate
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + step, max_af)

    return pd.Series(sar, index=df.index), pd.Series(trend, index=df.index)


def dots_below_price(df: pd.DataFrame, step: float = DEFAULT_STEP,
                      max_af: float = DEFAULT_MAX_AF) -> pd.Series:
    """BOPIS's exact condition: "Parabolic SAR dots below the candle" —
    the bullish-trend state."""
    _, trend = parabolic_sar(df, step, max_af)
    return trend == 1


def dots_above_price(df: pd.DataFrame, step: float = DEFAULT_STEP,
                      max_af: float = DEFAULT_MAX_AF) -> pd.Series:
    _, trend = parabolic_sar(df, step, max_af)
    return trend == -1


def compute_parabolic_sar(df: pd.DataFrame, step: float = DEFAULT_STEP,
                           max_af: float = DEFAULT_MAX_AF) -> pd.DataFrame:
    d = df.copy()
    d["psar"], d["psar_trend"] = parabolic_sar(d, step, max_af)
    d["psar_dots_below"] = d["psar_trend"] == 1
    d["psar_dots_above"] = d["psar_trend"] == -1
    return d
