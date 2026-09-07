"""
Moving Average family — SMA, EMA, ALMA, and Envelope (basis + % bands).

Built for "The Forbidden Book" strategy set (MAMA, CALMA, PAPA, TITA, and
Day Trading all use ALMA as their core support/resistance line; PAPA also
uses Envelope). All backward-looking by construction (plain `.rolling()`/
`.ewm()`), no lookahead risk.

ALMA (Arnaud Legoux Moving Average) parameters: the book repeatedly says
"default setting" without giving numbers. TradingView's ALMA defaults —
window=9, offset=0.85, sigma=6 — are used here, since TradingView is the
platform this book's chart studies are built around (its indicator
descriptions and terminology throughout match TradingView's). Flagged
explicitly as an assumption, not verified against the book's own source.
"""

import numpy as np
import pandas as pd

DEFAULT_ALMA_WINDOW = 9
DEFAULT_ALMA_OFFSET = 0.85
DEFAULT_ALMA_SIGMA = 6.0
DEFAULT_ENVELOPE_LENGTH = 40
DEFAULT_ENVELOPE_PERCENT = 3.0


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def alma(series: pd.Series, window: int = DEFAULT_ALMA_WINDOW,
          offset: float = DEFAULT_ALMA_OFFSET, sigma: float = DEFAULT_ALMA_SIGMA) -> pd.Series:
    """Gaussian-weighted moving average, weights skewed toward the recent
    end of the window by `offset` (0=skewed to oldest, 1=skewed to
    newest — TradingView's 0.85 leans toward recent/responsive) and
    shaped by `sigma` (smoothness). A plain rolling weighted average —
    backward-looking by construction, no different in kind from SMA."""
    m = offset * (window - 1)
    s = window / sigma
    idx = np.arange(window)
    weights = np.exp(-((idx - m) ** 2) / (2 * s ** 2))
    weights = weights / weights.sum()

    def _weighted(x):
        return np.dot(x, weights)

    return series.rolling(window).apply(_weighted, raw=True)


def envelope(series: pd.Series, length: int = DEFAULT_ENVELOPE_LENGTH,
             percent: float = DEFAULT_ENVELOPE_PERCENT, basis: str = "ema") -> tuple:
    """Returns (basis_line, upper, lower). `basis="ema"` matches PAPA's
    "click Exponential" instruction; `basis="sma"` also supported."""
    basis_line = ema(series, length) if basis == "ema" else sma(series, length)
    upper = basis_line * (1 + percent / 100)
    lower = basis_line * (1 - percent / 100)
    return basis_line, upper, lower


def compute_moving_averages(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                             alma_offset: float = DEFAULT_ALMA_OFFSET, alma_sigma: float = DEFAULT_ALMA_SIGMA,
                             envelope_length: int = DEFAULT_ENVELOPE_LENGTH,
                             envelope_percent: float = DEFAULT_ENVELOPE_PERCENT) -> pd.DataFrame:
    d = df.copy()
    d["ma_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)
    basis, upper, lower = envelope(d["close"], envelope_length, envelope_percent)
    d["ma_envelope_basis"] = basis
    d["ma_envelope_upper"] = upper
    d["ma_envelope_lower"] = lower
    return d
