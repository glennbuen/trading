"""
Strategy B: Breakout + Retest (architecture spec §10).

Sequence:
  1. Established level    — a confirmed swing high (resistance) or swing
                             low (support) from market_structure. Not an
                             arbitrary rolling window — real structure.
  2. Breakout              — price closes beyond the level
                             (market_structure.break_of_structure_up/down)
                             WITH volume expansion on that candle.
  3. Retest                — within `retest_window` bars after the
                             breakout, price pulls back and touches back
                             at/near the broken level.
  4. Rejection/acceptance  — the retest bar does NOT close back beyond the
                             level (price holds it as new support/
                             resistance). A bullish/bearish rejection
                             candle at the retest is recorded as extra
                             context but NOT required — requiring it would
                             make an already multi-stage pattern
                             vanishingly rare (the lesson from this repo's
                             earlier standalone bots: stacking too many
                             simultaneous conditions kills sample size).
  5. Volume confirmation   — the continuation bar (the one that actually
                             fires entry) shows volume expansion again.
  6. Continuation          — price closes beyond the highest/lowest point
                             reached since the breakout, confirming the
                             setup rather than merely "hasn't failed yet".

Implementation note: unlike the engines (one row -> one deterministic
value), this pattern spans a variable number of bars between breakout and
confirmation. It's implemented as a single vectorized pass using
`groupby(episode_id).cummax()/.cumsum()` rather than an explicit
bar-by-bar Python loop — every operation used (cumsum, cummax, shift,
ffill) only ever looks backward within an episode, so this stays
deterministic and lookahead-safe by the same construction rules as the
engines it's built from. See tests/test_breakout_retest.py for the
hand-built synthetic scenario and its truncation-invariance check.

No lookahead: every engine value consumed here (market_structure's
confirmed swing levels, price_action, volume) is already lookahead-safe in
its own module — see docs/ARCHITECTURE.md. This module adds no new
temporal risk, only sequencing logic over already-safe columns.
"""

import pandas as pd

from cryptobot.utils import bars_since
from cryptobot.engines import market_structure as ms
from cryptobot.engines import price_action as pa
from cryptobot.engines import volume as vol

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_VOLUME_LOOKBACK = vol.DEFAULT_LOOKBACK
DEFAULT_VOLUME_THRESHOLD = vol.DEFAULT_EXPANSION_THRESHOLD
DEFAULT_RETEST_WINDOW = 10
DEFAULT_RETEST_TOLERANCE_PCT = 0.01


def _scan_one_direction(df: pd.DataFrame, breakout_event: pd.Series, level: pd.Series,
                         touch_col: pd.Series, close_col: pd.Series, extreme_col: pd.Series,
                         held_above: bool, retest_window: int, retest_tolerance_pct: float,
                         volume_threshold: float, volume_lookback: int) -> pd.DataFrame:
    """
    Shared machinery for both directions. `held_above=True` for the
    bullish case (retest must hold ABOVE the level, continuation is a new
    HIGH); False for bearish (hold BELOW, continuation is a new LOW).
    """
    episode_id = breakout_event.cumsum()
    in_episode = episode_id > 0

    active_level = level.where(breakout_event).ffill()

    since_breakout = bars_since(breakout_event)
    if held_above:
        touched = touch_col <= active_level * (1 + retest_tolerance_pct)
        held = close_col >= active_level
    else:
        touched = touch_col >= active_level * (1 - retest_tolerance_pct)
        held = close_col <= active_level

    retest_touch = touched & held & (since_breakout >= 1) & (since_breakout <= retest_window) & in_episode
    retested_in_episode = retest_touch.groupby(episode_id).cummax().astype(bool)

    prior_extreme = extreme_col.groupby(episode_id).cummax().shift(1) if held_above \
        else extreme_col.groupby(episode_id).cummin().shift(1)

    volume_confirm = vol.is_volume_expansion(df, volume_lookback, volume_threshold)
    continuation = (close_col > prior_extreme) if held_above else (close_col < prior_extreme)

    confirmation_raw = retested_in_episode & continuation & volume_confirm & in_episode
    is_first_in_episode = confirmation_raw.groupby(episode_id).cumsum() == 1
    entry_signal = confirmation_raw & is_first_in_episode

    result = pd.DataFrame(index=df.index)
    result["episode_id"] = episode_id
    result["breakout_event"] = breakout_event
    result["active_level"] = active_level
    result["retest_touch"] = retest_touch
    result["retested_in_episode"] = retested_in_episode
    result["volume_confirm"] = volume_confirm
    result["entry_signal"] = entry_signal
    return result


def scan_breakout_retest_bullish(df: pd.DataFrame,
                                  structure_left: int = DEFAULT_STRUCTURE_LEFT,
                                  structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                                  volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                                  volume_threshold: float = DEFAULT_VOLUME_THRESHOLD,
                                  retest_window: int = DEFAULT_RETEST_WINDOW,
                                  retest_tolerance_pct: float = DEFAULT_RETEST_TOLERANCE_PCT) -> pd.DataFrame:
    level = ms.resistance(df, structure_left, structure_right).shift(1)
    breakout_event = (ms.break_of_structure_up(df, structure_left, structure_right) &
                      vol.is_volume_expansion(df, volume_lookback, volume_threshold))
    result = _scan_one_direction(
        df, breakout_event, level,
        touch_col=df["low"], close_col=df["close"], extreme_col=df["high"],
        held_above=True, retest_window=retest_window,
        retest_tolerance_pct=retest_tolerance_pct,
        volume_threshold=volume_threshold, volume_lookback=volume_lookback,
    )
    # Extra context for scoring/journaling later — NOT gating entry (see
    # module docstring on why rejection candles aren't required).
    result["retest_rejection_candle"] = pa.is_bullish_rejection(df) & result["retest_touch"]
    return result


def scan_breakout_retest_bearish(df: pd.DataFrame,
                                  structure_left: int = DEFAULT_STRUCTURE_LEFT,
                                  structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                                  volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                                  volume_threshold: float = DEFAULT_VOLUME_THRESHOLD,
                                  retest_window: int = DEFAULT_RETEST_WINDOW,
                                  retest_tolerance_pct: float = DEFAULT_RETEST_TOLERANCE_PCT) -> pd.DataFrame:
    level = ms.support(df, structure_left, structure_right).shift(1)
    breakout_event = (ms.break_of_structure_down(df, structure_left, structure_right) &
                      vol.is_volume_expansion(df, volume_lookback, volume_threshold))
    result = _scan_one_direction(
        df, breakout_event, level,
        touch_col=df["high"], close_col=df["close"], extreme_col=df["low"],
        held_above=False, retest_window=retest_window,
        retest_tolerance_pct=retest_tolerance_pct,
        volume_threshold=volume_threshold, volume_lookback=volume_lookback,
    )
    result["retest_rejection_candle"] = pa.is_bearish_rejection(df) & result["retest_touch"]
    return result


def compute_breakout_retest(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                             structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                             volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                             volume_threshold: float = DEFAULT_VOLUME_THRESHOLD,
                             retest_window: int = DEFAULT_RETEST_WINDOW,
                             retest_tolerance_pct: float = DEFAULT_RETEST_TOLERANCE_PCT) -> pd.DataFrame:
    """Convenience: both directions attached to a copy of df, prefixed
    br_long_ / br_short_."""
    d = df.copy()
    kwargs = dict(structure_left=structure_left, structure_right=structure_right,
                  volume_lookback=volume_lookback, volume_threshold=volume_threshold,
                  retest_window=retest_window, retest_tolerance_pct=retest_tolerance_pct)
    long_result = scan_breakout_retest_bullish(df, **kwargs)
    short_result = scan_breakout_retest_bearish(df, **kwargs)
    for col in long_result.columns:
        d[f"br_long_{col}"] = long_result[col]
    for col in short_result.columns:
        d[f"br_short_{col}"] = short_result[col]
    return d
