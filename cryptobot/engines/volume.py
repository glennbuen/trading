"""
Volume Engine — relative volume, spikes, expansion/contraction.

Per the architecture brief (§9): Relative Volume = Current Volume /
Average Volume, with configurable thresholds (1.2x, 1.5x, 2.0x, 3.0x) —
this module makes no claim about which threshold is "best"; that's for
backtesting to determine, not this engine to assume.

A NOTE ON WHAT "NO LOOKAHEAD" MEANS HERE, to avoid conflating two
different concerns (this distinction is also called out in
docs/ARCHITECTURE.md): `volume_baseline` compares each bar's volume to
the average of the PRECEDING N bars (`.shift(1).rolling(N)`), excluding
the current bar. This is NOT a temporal lookahead fix — a plain
`.rolling(N).mean()` including the current bar would still only use data
up to and including the current bar, which is fully causal and knowable
the moment that bar closes. Excluding the current bar is a DESIGN CHOICE
for a cleaner anomaly definition: an unusually huge volume bar shouldn't
be allowed to inflate its own baseline and make itself look average. Both
choices are lookahead-safe; this module picks the more standard one for
"is this bar anomalous" questions, for consistency with
price_action.relative_candle_size, which makes the same choice for the
same reason.

Breakout-volume and pullback-volume (spec §9) are compositions of this
engine's output with price_action/market_structure signals (e.g. "is this
breakout candle also a volume expansion candle") — deliberately NOT
implemented here, to keep this engine single-purpose. That composition
belongs to the strategy layer (Phase 4).
"""

import numpy as np
import pandas as pd

DEFAULT_LOOKBACK = 20
DEFAULT_EXPANSION_THRESHOLD = 1.2
DEFAULT_SPIKE_THRESHOLD = 2.0
DEFAULT_CONTRACTION_THRESHOLD = 0.7


def volume_baseline(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    """Average volume of the PRECEDING `lookback` bars (current excluded).
    See module docstring for why current is excluded here."""
    return df["volume"].shift(1).rolling(lookback).mean()


def relative_volume(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK) -> pd.Series:
    """Current Volume / Average Volume, per spec §9."""
    baseline = volume_baseline(df, lookback)
    return df["volume"] / baseline.replace(0, np.nan)


def is_volume_expansion(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                         threshold: float = DEFAULT_EXPANSION_THRESHOLD) -> pd.Series:
    """Moderately above-average participation. Threshold is configurable
    and deliberately not asserted as "correct" — test different values."""
    return (relative_volume(df, lookback) >= threshold).fillna(False)


def is_volume_spike(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                     threshold: float = DEFAULT_SPIKE_THRESHOLD) -> pd.Series:
    """Extreme above-average participation. Not mutually exclusive with
    is_volume_expansion — a spike is (by sane threshold choices) also an
    expansion; these are two configurable severity tiers, not categories."""
    return (relative_volume(df, lookback) >= threshold).fillna(False)


def is_volume_contraction(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                           threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.Series:
    """Below-average participation — e.g. a quiet, healthy pullback with
    low volume, or a dead/illiquid market, depending on context the
    strategy layer supplies."""
    return (relative_volume(df, lookback) <= threshold).fillna(False)


def is_volume_anomaly(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                       spike_threshold: float = DEFAULT_SPIKE_THRESHOLD,
                       contraction_threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.Series:
    """Either extreme — a spike OR a contraction — flagged as "unusual,
    look closer" without asserting a direction."""
    return (is_volume_spike(df, lookback, spike_threshold) |
            is_volume_contraction(df, lookback, contraction_threshold))


def volume_rising(df: pd.DataFrame, short: int = 5, long: int = DEFAULT_LOOKBACK) -> pd.Series:
    """Short-window volume average above the long-window average — a
    simple, standard MA-crossover trend read (both windows include the
    current bar; no self-referential-baseline concern here since we're
    comparing two averages to each other, not a value to its own
    baseline)."""
    return df["volume"].rolling(short).mean() > df["volume"].rolling(long).mean()


def volume_falling(df: pd.DataFrame, short: int = 5, long: int = DEFAULT_LOOKBACK) -> pd.Series:
    return df["volume"].rolling(short).mean() < df["volume"].rolling(long).mean()


def compute_volume(df: pd.DataFrame, lookback: int = DEFAULT_LOOKBACK,
                    expansion_threshold: float = DEFAULT_EXPANSION_THRESHOLD,
                    spike_threshold: float = DEFAULT_SPIKE_THRESHOLD,
                    contraction_threshold: float = DEFAULT_CONTRACTION_THRESHOLD) -> pd.DataFrame:
    """Convenience: compute every volume column at once."""
    d = df.copy()
    d["vol_baseline"] = volume_baseline(d, lookback)
    d["vol_relative"] = relative_volume(d, lookback)
    d["vol_expansion"] = is_volume_expansion(d, lookback, expansion_threshold)
    d["vol_spike"] = is_volume_spike(d, lookback, spike_threshold)
    d["vol_contraction"] = is_volume_contraction(d, lookback, contraction_threshold)
    d["vol_anomaly"] = is_volume_anomaly(d, lookback, spike_threshold, contraction_threshold)
    d["vol_rising"] = volume_rising(d)
    d["vol_falling"] = volume_falling(d)
    return d
