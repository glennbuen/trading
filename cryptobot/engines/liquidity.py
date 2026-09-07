"""
Liquidity Engine — equal highs/lows, range levels, and sweep-and-reclaim
detection: places where stops/orders are likely clustered, and objective
detection of when price sweeps through them and reverses.

Per the architecture brief (§8): "This must be objectively measurable and
backtestable. Do not use vague 'smart money' terminology unless it can be
converted into deterministic rules." Every function below is a plain,
inspectable rule over price data — no discretionary judgment calls.

Builds on market_structure's CONFIRMED swing series (never the raw,
lookahead-unsafe one — see market_structure.py's docstring) and reuses
price_action's rolling range levels rather than redefining them.

Volume confirmation for a sweep (the spec's own worked example folds in
"volume increases" as the final step) is deliberately NOT included here —
that's a cross-engine composition that belongs to the strategy layer
(Phase 4's liquidity-sweep-reversal strategy will combine
swept_and_reclaimed_above/below with volume.is_volume_expansion). Keeping
this engine to geometry only, with no opinion on which volume threshold
matters, mirrors the same single-responsibility split already used
between price_action and market_structure.
"""

import pandas as pd

from cryptobot.utils import bars_since
from cryptobot.engines import market_structure as ms
from cryptobot.engines.price_action import breakout_level_up, breakout_level_down

DEFAULT_LEFT = ms.DEFAULT_LEFT
DEFAULT_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_TOLERANCE_PCT = 0.05
DEFAULT_MAX_BARS_TO_RECLAIM = 3


def equal_highs(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT,
                 tolerance_pct: float = DEFAULT_TOLERANCE_PCT) -> pd.Series:
    """True when a newly confirmed swing high lands within `tolerance_pct`
    of the PREVIOUS confirmed swing high — price retested a prior high
    without decisively breaking it, the classic "equal highs" liquidity
    pool. Fires as an event at the confirmation bar, same convention as
    market_structure.higher_high/lower_high."""
    conf_val = ms.swing_high_confirmed_value(df, left, right)
    prior = ms.prior_confirmed_value(conf_val)
    close_enough = ((conf_val - prior).abs() / prior.replace(0, pd.NA)) <= tolerance_pct
    return (conf_val.notna() & prior.notna() & close_enough.fillna(False))


def equal_lows(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT,
               tolerance_pct: float = DEFAULT_TOLERANCE_PCT) -> pd.Series:
    conf_val = ms.swing_low_confirmed_value(df, left, right)
    prior = ms.prior_confirmed_value(conf_val)
    close_enough = ((conf_val - prior).abs() / prior.replace(0, pd.NA)) <= tolerance_pct
    return (conf_val.notna() & prior.notna() & close_enough.fillna(False))


def range_high(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    """Rolling N-bar high (of the PRECEDING N bars) as a liquidity level —
    re-exports price_action's breakout level under a liquidity-context
    name rather than redefining the same rolling-max logic twice."""
    return breakout_level_up(df, lookback)


def range_low(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    return breakout_level_down(df, lookback)


def swept_and_reclaimed_above(df: pd.DataFrame, level: pd.Series,
                               max_bars: int = DEFAULT_MAX_BARS_TO_RECLAIM) -> pd.Series:
    """
    Level-agnostic sweep+reclaim: pass ANY support/liquidity level series
    (a confirmed swing low, previous-day low, range low, equal-lows
    level...). True when price traded below `level` intrabar within the
    last `max_bars` (including the current bar — a same-bar sweep-and-
    close-back-above is the strongest version of this pattern, a long
    lower-wick rejection at the level) and has now closed back above it.

    The dip below must be FRESH — the prior bar's close was still at or
    above `level` — not just "still below it". Without this, a price that
    closes below the level for several consecutive bars would keep
    resetting the "bars since sweep" counter every single bar (since
    low <= close always, staying below in close means staying below in
    low too), making `max_bars` meaningless as a recency filter. Requiring
    freshness distinguishes a brief wick-and-reclaim from an established
    downtrend that happens to still be under the level.
    """
    was_at_or_above = df["close"].shift(1) >= level.shift(1)
    fresh_sweep = (df["low"] < level) & was_at_or_above.fillna(False)
    since_sweep = bars_since(fresh_sweep)
    return (since_sweep <= max_bars) & (df["close"] > level)


def swept_and_reclaimed_below(df: pd.DataFrame, level: pd.Series,
                               max_bars: int = DEFAULT_MAX_BARS_TO_RECLAIM) -> pd.Series:
    was_at_or_below = df["close"].shift(1) <= level.shift(1)
    fresh_sweep = (df["high"] > level) & was_at_or_below.fillna(False)
    since_sweep = bars_since(fresh_sweep)
    return (since_sweep <= max_bars) & (df["close"] < level)


def liquidity_sweep_reversal_bullish(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                                      right: int = DEFAULT_RIGHT,
                                      max_bars: int = DEFAULT_MAX_BARS_TO_RECLAIM) -> pd.Series:
    """
    Convenience: sweep of the confirmed swing low (structure-based
    support), reclaimed. Uses `.shift(1)` on the level — same convention
    as market_structure.break_of_structure_* — so the level being swept
    is the one that was already known as of the PRIOR bar, not one the
    sweeping bar's own low could itself have just updated.
    """
    level = ms.support(df, left, right).shift(1)
    return swept_and_reclaimed_above(df, level, max_bars)


def liquidity_sweep_reversal_bearish(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                                      right: int = DEFAULT_RIGHT,
                                      max_bars: int = DEFAULT_MAX_BARS_TO_RECLAIM) -> pd.Series:
    level = ms.resistance(df, left, right).shift(1)
    return swept_and_reclaimed_below(df, level, max_bars)


def compute_liquidity(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT,
                       tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
                       range_lookback: int = 20,
                       max_bars_to_reclaim: int = DEFAULT_MAX_BARS_TO_RECLAIM) -> pd.DataFrame:
    """Convenience: compute every liquidity column at once."""
    d = df.copy()
    d["liq_equal_highs"] = equal_highs(d, left, right, tolerance_pct)
    d["liq_equal_lows"] = equal_lows(d, left, right, tolerance_pct)
    d["liq_range_high"] = range_high(d, range_lookback)
    d["liq_range_low"] = range_low(d, range_lookback)
    d["liq_sweep_reversal_bullish"] = liquidity_sweep_reversal_bullish(d, left, right, max_bars_to_reclaim)
    d["liq_sweep_reversal_bearish"] = liquidity_sweep_reversal_bearish(d, left, right, max_bars_to_reclaim)
    return d
