"""
Volatility Engine — True Range / ATR.

Small and focused: needed by the backtest engine's ATR-based stop-loss
method (§18) and by regime detection later (§13 references high/low
volatility explicitly). Reuses the exact formula validated across all 7
standalone bots earlier in this project (Wilder smoothing via
ewm(alpha=1/length)) rather than inventing a new one.
"""

import pandas as pd

DEFAULT_ATR_LEN = 14


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, length: int = DEFAULT_ATR_LEN) -> pd.Series:
    """Wilder's ATR. Only ever uses bar <= i (ewm/shift are both
    backward-only), so this is lookahead-safe by the same construction
    rule as everything else in the package."""
    return true_range(df).ewm(alpha=1 / length, adjust=False).mean()


def atr_pct(df: pd.DataFrame, length: int = DEFAULT_ATR_LEN) -> pd.Series:
    """ATR as a percentage of price — comparable across symbols/price
    scales, unlike raw ATR."""
    return (atr(df, length) / df["close"]) * 100


def compute_volatility(df: pd.DataFrame, length: int = DEFAULT_ATR_LEN) -> pd.DataFrame:
    d = df.copy()
    d["vlt_true_range"] = true_range(d)
    d["vlt_atr"] = atr(d, length)
    d["vlt_atr_pct"] = atr_pct(d, length)
    return d
