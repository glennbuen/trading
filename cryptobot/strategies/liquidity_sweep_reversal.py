"""
Strategy D: Liquidity Sweep Reversal (architecture spec §10).

Sequence:
  1. Important previous high/low  — a confirmed structural swing level
                                     (market_structure.support/resistance)
                                     or a prior-day level
                                     (market_structure.previous_day_levels)
                                     — configurable, since the spec lists
                                     both as valid "important" levels.
  2. Sweep                         — price trades through the level
                                     intrabar (liquidity.swept_and_
                                     reclaimed_above/below already
                                     implements exactly this "fresh dip
                                     from above/below, not an already-
                                     established move" geometry — see
                                     that module's docstring for why
                                     freshness matters).
  3. Rejection                     — the sweep bar (or one shortly after)
                                     closes back on the origin side.
  4. Reclaim                       — same mechanism as #3 in this
                                     implementation: liquidity.swept_and_
                                     reclaimed_* already requires the
                                     close to have reclaimed the level,
                                     so "rejection" and "reclaim" collapse
                                     into one condition here rather than
                                     two — a deliberate simplification,
                                     not a missing step.
  5. Market-structure shift        — the reclaim must occur while the
                                     PRIOR trend context was NOT already
                                     in the reclaim's direction (i.e. this
                                     is presented as a genuine reversal
                                     setup, not just "buying a dip in an
                                     uptrend" — which is Strategy C's job).
                                     Concretely: trend_state was 'down' or
                                     'transition' (not already 'up') for a
                                     bullish reversal, and vice versa.
  6. Volume confirmation           — volume.is_volume_expansion on the
                                     reclaim bar, per the spec's own
                                     worked example ("Volume increases").

Single-bar signal (no multi-bar episode tracking needed) — the sweep-and-
reclaim geometry itself already spans the bars it needs via
liquidity.swept_and_reclaimed_above/below's internal max_bars window, so
this strategy just ANDs that with the two additional conditions (was NOT
already trending that way, and volume confirms) on the same bar the
reclaim fires.

No lookahead: every column consumed here is already lookahead-safe in its
own engine (see docs/ARCHITECTURE.md and liquidity.py's own docstring on
its `.shift(1)`-based level convention). This module adds no new temporal
decisions.
"""

import pandas as pd

from cryptobot.engines import market_structure as ms
from cryptobot.engines import liquidity as liq
from cryptobot.engines import volume as vol

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_MAX_BARS_TO_RECLAIM = liq.DEFAULT_MAX_BARS_TO_RECLAIM
DEFAULT_VOLUME_LOOKBACK = vol.DEFAULT_LOOKBACK
DEFAULT_VOLUME_THRESHOLD = vol.DEFAULT_EXPANSION_THRESHOLD


def compute_liquidity_sweep_reversal(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                                      structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                                      max_bars_to_reclaim: int = DEFAULT_MAX_BARS_TO_RECLAIM,
                                      volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                                      volume_threshold: float = DEFAULT_VOLUME_THRESHOLD) -> pd.DataFrame:
    d = df.copy()

    trend = ms.trend_state(d, structure_left, structure_right)
    # The trend read as of the PRIOR bar — the reclaim bar's own close
    # shouldn't be allowed to retroactively justify itself as "not
    # already trending that way".
    prior_trend = trend.shift(1)

    sweep_reversal_bullish = liq.liquidity_sweep_reversal_bullish(
        d, structure_left, structure_right, max_bars_to_reclaim)
    sweep_reversal_bearish = liq.liquidity_sweep_reversal_bearish(
        d, structure_left, structure_right, max_bars_to_reclaim)

    not_already_up = prior_trend != "up"
    not_already_down = prior_trend != "down"
    volume_confirm = vol.is_volume_expansion(d, volume_lookback, volume_threshold)

    d["lsr_prior_trend"] = prior_trend
    d["lsr_sweep_reversal_bullish"] = sweep_reversal_bullish
    d["lsr_sweep_reversal_bearish"] = sweep_reversal_bearish
    d["lsr_volume_confirm"] = volume_confirm

    d["long_signal"] = sweep_reversal_bullish & not_already_up & volume_confirm
    d["short_signal"] = sweep_reversal_bearish & not_already_down & volume_confirm
    return d
