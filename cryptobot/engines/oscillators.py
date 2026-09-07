"""
Oscillator family — RSI, CCI, Fisher Transform, Trix.

Built for "The Forbidden Book" strategy set (TITA uses RSI; CALMA uses
CCI; FISHBALL uses Fisher Transform + Trix; BOPIS uses Trix).

Fisher Transform is the one recursive indicator here (each bar's value
depends on the PREVIOUS bar's already-computed value, same as this
project's earlier standalone bots' SuperTrend) — implemented as an
explicit bar-by-bar loop rather than a vectorized pandas expression,
since a true recursion can't be vectorized cleanly. Still fully
backward-looking: bar i only ever uses data/values from bars <= i.
"""

import numpy as np
import pandas as pd

DEFAULT_RSI_LENGTH = 14
DEFAULT_CCI_LENGTH = 20
DEFAULT_FISHER_LENGTH = 9
DEFAULT_TRIX_LENGTH = 18


def rsi(series: pd.Series, length: int = DEFAULT_RSI_LENGTH) -> pd.Series:
    """Wilder's RSI, reformulated the same way as
    money_flow_index.money_flow_index (algebraically identical to the
    classic 100 - 100/(1+avg_gain/avg_loss), caught by testing here too:
    a strictly rising series has avg_loss==0, and the classic ratio
    formula's avg_gain/0 -> NaN -> a spurious neutral-50 fallback, when
    the mathematically correct answer is 100 (maximally overbought, all
    gains). 100*avg_gain/(avg_gain+avg_loss) gives 100 in that case
    correctly, and still falls through to a genuine neutral 50 only when
    there's truly zero movement (both sums zero)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    total = avg_gain + avg_loss
    return (100 * avg_gain / total.replace(0, np.nan)).fillna(50)


def cci(df: pd.DataFrame, length: int = DEFAULT_CCI_LENGTH) -> pd.Series:
    """Commodity Channel Index: (typical price - its SMA) / (0.015 x mean
    absolute deviation of typical price), both over the trailing `length`
    bars — a plain rolling calculation, backward-looking by construction."""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    tp_sma = tp.rolling(length).mean()
    mad = tp.rolling(length).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (tp - tp_sma) / (0.015 * mad.replace(0, np.nan))


def fisher_transform(df: pd.DataFrame, length: int = DEFAULT_FISHER_LENGTH) -> tuple:
    """Returns (fisher, trigger). Ehlers' Fisher Transform: normalizes
    the median price to [-1, 1] against its own trailing `length`-bar
    range, smooths recursively, then applies the inverse-hyperbolic-
    tangent-style transform (also recursive). `trigger` is fisher lagged
    by 1 bar, the standard convention for reading crosses."""
    median_price = (df["high"] + df["low"]) / 2
    max_h = median_price.rolling(length).max()
    min_l = median_price.rolling(length).min()
    rng = (max_h - min_l).replace(0, np.nan)

    n = len(df)
    value = np.zeros(n)
    fisher = np.zeros(n)
    mp = median_price.values
    mx = max_h.values
    mn = min_l.values
    rv = rng.values

    for i in range(n):
        if np.isnan(mx[i]) or np.isnan(mn[i]) or np.isnan(rv[i]):
            value[i] = 0.0
            fisher[i] = fisher[i - 1] if i > 0 else 0.0
            continue
        raw = 2 * ((mp[i] - mn[i]) / rv[i] - 0.5)
        prev_value = value[i - 1] if i > 0 else 0.0
        v = 0.33 * raw + 0.67 * prev_value
        v = min(max(v, -0.999), 0.999)
        value[i] = v
        prev_fisher = fisher[i - 1] if i > 0 else 0.0
        fisher[i] = 0.5 * np.log((1 + v) / (1 - v)) + 0.5 * prev_fisher

    fisher_s = pd.Series(fisher, index=df.index)
    trigger_s = fisher_s.shift(1)
    return fisher_s, trigger_s


def trix(series: pd.Series, length: int = DEFAULT_TRIX_LENGTH) -> pd.Series:
    """Triple-smoothed EMA rate of change, as a percentage."""
    ema1 = series.ewm(span=length, adjust=False).mean()
    ema2 = ema1.ewm(span=length, adjust=False).mean()
    ema3 = ema2.ewm(span=length, adjust=False).mean()
    return (ema3 - ema3.shift(1)) / ema3.shift(1).replace(0, np.nan) * 100


def trix_cross_up_zero(series: pd.Series, length: int = DEFAULT_TRIX_LENGTH) -> pd.Series:
    t = trix(series, length)
    above = t > 0
    was_above = above.shift(1).fillna(False).astype(bool)  # see ichimoku.py's docstring on why this cast matters
    return above & ~was_above


def trix_cross_down_zero(series: pd.Series, length: int = DEFAULT_TRIX_LENGTH) -> pd.Series:
    t = trix(series, length)
    below = t < 0
    was_below = below.shift(1).fillna(False).astype(bool)
    return below & ~was_below


def compute_oscillators(df: pd.DataFrame, rsi_length: int = DEFAULT_RSI_LENGTH,
                         cci_length: int = DEFAULT_CCI_LENGTH, fisher_length: int = DEFAULT_FISHER_LENGTH,
                         trix_length: int = DEFAULT_TRIX_LENGTH) -> pd.DataFrame:
    d = df.copy()
    d["osc_rsi"] = rsi(d["close"], rsi_length)
    d["osc_cci"] = cci(d, cci_length)
    d["osc_fisher"], d["osc_fisher_trigger"] = fisher_transform(d, fisher_length)
    d["osc_trix"] = trix(d["close"], trix_length)
    return d
