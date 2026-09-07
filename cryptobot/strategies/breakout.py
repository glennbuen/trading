"""
Strategy A: Breakout (architecture spec §10).

Detects: consolidation -> defined range/resistance/support -> breakout ->
breakout strength -> volume confirmation. Unlike Breakout+Retest
(Strategy B, Phase 4), this enters ON the breakout itself with no wait
for a retest — the natural "control" comparison: does requiring a
retest+hold actually improve on a raw, volume-confirmed breakout, or was
the retest requirement mostly filtering out trades either way? (a direct
question for Phase 11's strategy comparison).

Consolidation ("reject weak breakouts where appropriate", spec §10, made
concrete rather than left vague): the bar immediately BEFORE a breakout
must have had its ATR sitting in a below-`percentile` rank of its own
trailing history — a volatility contraction. A breakout emerging from an
already-quiet market is a qualitatively different, more analyzable event
than one firing amid already-elevated volatility. Checked on the PRIOR
bar (`.shift(1)`), not the breakout bar itself — the breakout bar's own
ATR is often already elevated by the move that defines it, so requiring
consolidation ON that same bar would almost never fire.

Breakout: BOTH a confirmed structural break (market_structure's
swing-based resistance/support — the real "established level", no
lookahead) AND a simple rolling-range breakout
(price_action.is_breakout_up/down) must agree — two independently
computed breakout definitions concluding the same thing is stronger
confirmation than either alone.

Breakout strength / follow-through: the breakout candle itself must be a
"strong" candle (price_action.is_strong_bullish/bearish — large body
relative to its own range and recent history), not a thin poke through
the level.

Volume confirmation: volume.is_volume_expansion on the breakout candle.

No lookahead: every column consumed here is already lookahead-safe in its
own engine (see docs/ARCHITECTURE.md). This is a single-bar AND of
already-safe columns — no multi-bar episode tracking needed, unlike
Breakout+Retest.
"""

import pandas as pd

from cryptobot.engines import market_structure as ms
from cryptobot.engines import price_action as pa
from cryptobot.engines import volume as vol
from cryptobot.engines import volatility as vlt

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_CONSOLIDATION_LOOKBACK = 50
DEFAULT_CONSOLIDATION_PERCENTILE = 0.4
DEFAULT_BREAKOUT_LOOKBACK = pa.DEFAULT_LOOKBACK
DEFAULT_VOLUME_LOOKBACK = vol.DEFAULT_LOOKBACK
DEFAULT_VOLUME_THRESHOLD = vol.DEFAULT_EXPANSION_THRESHOLD
DEFAULT_ATR_LEN = vlt.DEFAULT_ATR_LEN


def is_consolidating(df: pd.DataFrame, atr_len: int = DEFAULT_ATR_LEN,
                      lookback: int = DEFAULT_CONSOLIDATION_LOOKBACK,
                      percentile: float = DEFAULT_CONSOLIDATION_PERCENTILE) -> pd.Series:
    """True when the current bar's ATR ranks at or below `percentile`
    within its own trailing `lookback`-bar window (including itself — a
    plain rolling window, fully backward-looking by construction, so this
    needs no self-reference-avoidance shift the way volume/candle-size
    baselines do)."""
    # Strict less-than, not <=: on a perfectly flat/tied window every
    # value equals the last one, and <= would count all of them as "at or
    # below" it, ranking a completely flat market at the TOP of its own
    # range instead of the bottom — backwards from what "consolidating"
    # should mean. Strict < correctly ranks a tied/flat window at 0 (the
    # bottom), matching the convention already used elsewhere in this
    # project (the standalone bots' adaptive-ATR-multiplier logic).
    atr = vlt.atr(df, atr_len)
    pct_rank = atr.rolling(lookback).apply(lambda w: (w < w.iloc[-1]).mean(), raw=False)
    return (pct_rank <= percentile).fillna(False)


def compute_breakout(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                      structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                      consolidation_lookback: int = DEFAULT_CONSOLIDATION_LOOKBACK,
                      consolidation_percentile: float = DEFAULT_CONSOLIDATION_PERCENTILE,
                      breakout_lookback: int = DEFAULT_BREAKOUT_LOOKBACK,
                      volume_lookback: int = DEFAULT_VOLUME_LOOKBACK,
                      volume_threshold: float = DEFAULT_VOLUME_THRESHOLD,
                      atr_len: int = DEFAULT_ATR_LEN) -> pd.DataFrame:
    d = df.copy()

    was_consolidating = is_consolidating(d, atr_len, consolidation_lookback,
                                          consolidation_percentile).shift(1).fillna(False)
    structural_break_up = ms.break_of_structure_up(d, structure_left, structure_right)
    structural_break_down = ms.break_of_structure_down(d, structure_left, structure_right)
    range_break_up = pa.is_breakout_up(d, breakout_lookback)
    range_break_down = pa.is_breakout_down(d, breakout_lookback)
    strong_up = pa.is_strong_bullish(d)
    strong_down = pa.is_strong_bearish(d)
    volume_confirm = vol.is_volume_expansion(d, volume_lookback, volume_threshold)

    d["bo_was_consolidating"] = was_consolidating
    d["bo_structural_break_up"] = structural_break_up
    d["bo_structural_break_down"] = structural_break_down
    d["bo_range_break_up"] = range_break_up
    d["bo_range_break_down"] = range_break_down
    d["bo_strong_candle_up"] = strong_up
    d["bo_strong_candle_down"] = strong_down
    d["bo_volume_confirm"] = volume_confirm

    d["long_signal"] = (was_consolidating & structural_break_up & range_break_up &
                        strong_up & volume_confirm)
    d["short_signal"] = (was_consolidating & structural_break_down & range_break_down &
                         strong_down & volume_confirm)
    return d
