"""
Structure Break Engine — the "valid low / valid high" market-structure
definition from the user's own transcript of a YouTube trading video
("a 3-step formula... step 1: market structure"), NOT this project's
existing `market_structure.trend_state()` (a different, simpler
definition already used by 4 other strategies).

The video's rule, precisely: a swing low is only a VALID structural
reference (the level that must break to flip the trend down) once price,
after making that low, goes on to break above the swing high that
preceded it. Until that happens, any newer local low that forms without
first breaking a prior high is explicitly NOT validated and must be
ignored — "we are still looking at our previous low... so we are still
in an uptrend" is the video's own worked example of exactly this case.
The video also gives a second, separate example of `valid_low` itself
advancing: once already in an uptrend, breaking a SUBSEQUENT confirmed
high "transfers" valid_low forward to the newer pullback low that
preceded that break. Symmetric for downtrends/valid highs throughout.

This is a genuinely different (and genuinely recursive) definition from
`market_structure.trend_state()`, which classifies trend from independent
higher-high/higher-low comparisons with no such validation/advancement
step, and is why this needed its own engine. It IS built entirely on top
of `market_structure`'s already-tested, lookahead-safe primitives — no
new swing-detection logic, only a new state machine layered over
`support()`/`resistance()` (confirmed swing levels) and the already
edge-triggered `break_of_structure_up`/`break_of_structure_down` — a
genuinely recursive bar-by-bar loop, same category as `parabolic_sar.py`
(each bar's state depends on prior state, but only ever on state derived
from bars < i, so it remains fully backward-looking).

Two DECOUPLED roles, both required — collapsing them into one would
silently reproduce the exact mistake the video is about:

  1. `break_of_structure_up`/`_down` (breaking the most recently
     CONFIRMED swing high/low) only ever BOOTSTRAPS the very first trend
     from "undefined", or ADVANCES (trails) the current valid_low/high
     forward while a trend is ALREADY established in that direction —
     it is explicitly ignored as a trend-FLIP trigger (an uptrend does
     not flip to "down" just because `break_of_structure_down` fires;
     that level may have trailed up above the true valid_low, which is
     exactly the unvalidated-pullback-low trap the video names).
  2. A trend actually FLIPS only when price closes below the CURRENT
     `valid_low` (or above `valid_high`) directly — a check entirely
     decoupled from `market_structure.support()`/`resistance()`'s own
     continuous trailing, which is precisely why `valid_low` is NOT
     simply `market_structure.support()` re-exported.
"""

import numpy as np
import pandas as pd

from cryptobot.engines import market_structure as ms

DEFAULT_LEFT = ms.DEFAULT_LEFT
DEFAULT_RIGHT = ms.DEFAULT_RIGHT


def compute_structure_break(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                             right: int = DEFAULT_RIGHT) -> pd.DataFrame:
    d = df.copy()
    support = ms.support(d, left, right)
    resistance = ms.resistance(d, left, right)
    bos_up = ms.break_of_structure_up(d, left, right)
    bos_down = ms.break_of_structure_down(d, left, right)

    close = d["close"].values
    support_vals = support.values
    resistance_vals = resistance.values
    bos_up_vals = bos_up.values
    bos_down_vals = bos_down.values

    n = len(d)
    trend = np.zeros(n, dtype=int)         # 0=undefined, 1=up, -1=down
    valid_low = np.full(n, np.nan)
    valid_high = np.full(n, np.nan)

    cur_trend = 0
    cur_valid_low = np.nan
    cur_valid_high = np.nan

    for i in range(n):
        if cur_trend == 1 and not np.isnan(cur_valid_low) and close[i] < cur_valid_low:
            # The ONLY event that flips an uptrend to a downtrend: price
            # directly closes below the current (fixed, non-trailing)
            # valid_low — never a mere break_of_structure_down, which may
            # be referencing a shallower, unvalidated pullback low.
            cur_trend = -1
            if not np.isnan(resistance_vals[i]):
                cur_valid_high = resistance_vals[i]
        elif cur_trend == -1 and not np.isnan(cur_valid_high) and close[i] > cur_valid_high:
            cur_trend = 1
            if not np.isnan(support_vals[i]):
                cur_valid_low = support_vals[i]
        elif bos_up_vals[i] and cur_trend != -1:
            # Bootstraps the first-ever uptrend (cur_trend==0), or
            # ADVANCES valid_low forward during an ongoing uptrend
            # (cur_trend==1) per the video's own "transferred" example.
            # Deliberately excluded while cur_trend==-1 (a downtrend only
            # ever flips via the direct valid_high breach above).
            cur_trend = 1
            if not np.isnan(support_vals[i]):
                cur_valid_low = support_vals[i]
        elif bos_down_vals[i] and cur_trend != 1:
            cur_trend = -1
            if not np.isnan(resistance_vals[i]):
                cur_valid_high = resistance_vals[i]

        trend[i] = cur_trend
        valid_low[i] = cur_valid_low
        valid_high[i] = cur_valid_high

    d["sb_valid_low"] = valid_low
    d["sb_valid_high"] = valid_high
    d["sb_trend"] = pd.Series(np.where(trend == 1, "up", np.where(trend == -1, "down", "undefined")),
                               index=d.index)
    d["sb_trend_up"] = trend == 1
    d["sb_trend_down"] = trend == -1
    return d
