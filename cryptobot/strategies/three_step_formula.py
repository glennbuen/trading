"""
"3-Step Formula" — from the user's own transcript of a YouTube trading
video (no strategy name given in the video itself; named here after how
the user introduced it: "I have a 3 step formula that I've backtested
1000s of times"). No indicators in the video's own framing beyond raw
price action — built here as a composition of already-tested engine
primitives, same approach as every other strategy this project has
built from a described (not coded) source.

Step 1 — Market structure: `engines/structure_break.py`'s `sb_trend`
(the video's own "valid low / valid high" definition — see that
module's docstring for why it's a different, more careful definition
than this project's existing `market_structure.trend_state()`). Only
`sb_trend=="up"` looks for demand zones/longs; only `"down"` looks for
supply zones/shorts — "we don't even consider supply zones because
we're in an uptrend," per the video.

Step 2 — Supply/demand zones: the video's own concrete, actionable rule
("mark the candle right before the impulse move... from the low to the
high of the previous candle") is implemented literally — the zone is the
[low, high] range of the candle immediately preceding an impulse candle
(`price_action.is_strong_bullish`/`is_strong_bearish`, already-tested
primitives, reused rather than redefined), gated on the CURRENT trend
direction at formation. The video's looser "area of consolidation"
language around this is descriptive scaffolding, not a separate testable
condition — flagged explicitly since it isn't implemented as its own
gate. Entry fires on the FIRST bar price re-enters the zone after it
forms (same first-touch-only convention as `support_20pct.py`), gated
again on trend still matching at the touch bar (a zone whose trend has
since flipped is treated as invalidated, not a literal instruction from
the video but a reasonable, non-arbitrary consequence of it).

Step 3 — Risk:reward filter: the video's own explicit numeric rule
("we only want to take trades if the risk to reward is above 2.5:1")
wired via `backtest.engine.StopTargetConfig`'s new `structure_target_col`
+ `min_rr` (added specifically for this strategy — see that module's
docstring). Stop = the zone's far boundary; target = "the recent highs"
/"recent lows" — the video's own words for its take-profit in every
worked example, read as the running max-high/min-low SINCE the zone
formed (the peak of the current move), NOT
`market_structure.resistance()`/`support()` (the fractal-CONFIRMED PRIOR
swing extreme). That distinction was a real bug caught during evaluation,
not a style choice: the confirmed prior swing high is, by construction,
the very level the impulse candle just broke through to form this zone,
so it's almost always already behind price by the time a retest entry
fires — using it made nearly every signal fail the RR filter for a
reason that had nothing to do with the strategy's actual merit. Caught
by inspecting a near-zero real-data trade count before drawing any
conclusion, and fixed before evaluating — not a case of loosening a
disappointing result, the opposite: fixing an implementation choice that
didn't match what the video actually describes.

Unlike every other deck/book-sourced strategy in this project (all
long-only, matching their PSE-retail origin where shorting isn't
practical for retail), this one is explicitly demonstrated with BOTH
long (demand) and short (supply) trades in the video's own walkthrough,
and this project's backtest engine already supports short positions —
so both sides are implemented here.
"""

import numpy as np
import pandas as pd

from cryptobot.engines import market_structure as ms
from cryptobot.engines.structure_break import compute_structure_break, DEFAULT_LEFT, DEFAULT_RIGHT
from cryptobot.engines.price_action import (
    is_strong_bullish, is_strong_bearish, DEFAULT_BODY_FRAC, DEFAULT_REL_SIZE, DEFAULT_LOOKBACK,
)

DEFAULT_MIN_RR = 2.5


def compute_three_step_formula(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT,
                                body_frac: float = DEFAULT_BODY_FRAC, min_rel_size: float = DEFAULT_REL_SIZE,
                                impulse_lookback: int = DEFAULT_LOOKBACK) -> pd.DataFrame:
    d = compute_structure_break(df, left, right)

    impulse_up = is_strong_bullish(d, body_frac, min_rel_size, impulse_lookback)
    impulse_down = is_strong_bearish(d, body_frac, min_rel_size, impulse_lookback)

    demand_forms = impulse_up & d["sb_trend_up"]
    supply_forms = impulse_down & d["sb_trend_down"]

    demand_low = d["low"].shift(1).where(demand_forms).ffill()
    demand_high = d["high"].shift(1).where(demand_forms).ffill()
    supply_low = d["low"].shift(1).where(supply_forms).ffill()
    supply_high = d["high"].shift(1).where(supply_forms).ffill()

    demand_episode = (demand_low != demand_low.shift(1)).cumsum()
    supply_episode = (supply_low != supply_low.shift(1)).cumsum()

    # "Recent highs"/"recent lows" (the video's own stated take-profit) is
    # the peak/trough of the CURRENT move — the running max high / min low
    # since this specific zone formed (tracked forward from the impulse
    # bar's own high/low, itself already known at that bar's close) — NOT
    # market_structure.resistance()/support(), the fractal-CONFIRMED prior
    # swing extreme. That distinction matters here specifically: the
    # confirmed prior swing high is, by construction, the very level the
    # impulse candle just broke through to form this zone in the first
    # place, so it is almost always already BEHIND price by the time a
    # retest entry fires — a real implementation bug caught by inspecting
    # near-zero real-data signal counts before drawing any conclusion, not
    # a case of loosening a disappointing result.
    recent_high = d["high"].groupby(demand_episode).cummax()
    recent_low = d["low"].groupby(supply_episode).cummin()

    # The formation (impulse) bar itself must never count as a "touch" —
    # its own low/high will almost always overlap the zone it just broke
    # away from (the zone is literally the immediately preceding candle's
    # range), which is not "price re-entering the zone later" at all, the
    # video's own stated entry condition. A real bug caught the same way
    # as the recent-highs one above: near-zero real-data trade counts,
    # inspected before drawing any conclusion.
    demand_touch = (d["low"] <= demand_high) & (d["high"] >= demand_low) & demand_low.notna() & ~demand_forms
    supply_touch = (d["high"] >= supply_low) & (d["low"] <= supply_high) & supply_low.notna() & ~supply_forms

    demand_touch_count = demand_touch.groupby(demand_episode).cumsum()
    supply_touch_count = supply_touch.groupby(supply_episode).cumsum()

    demand_first_touch = demand_touch & (demand_touch_count == 1)
    supply_first_touch = supply_touch & (supply_touch_count == 1)

    long_signal = demand_first_touch & d["sb_trend_up"]
    short_signal = supply_first_touch & d["sb_trend_down"]

    d["tsf_demand_low"] = demand_low
    d["tsf_demand_high"] = demand_high
    d["tsf_supply_low"] = supply_low
    d["tsf_supply_high"] = supply_high
    d["long_signal"] = long_signal.fillna(False)
    d["short_signal"] = short_signal.fillna(False)

    d["tsf_structure_stop"] = np.where(d["long_signal"], demand_low, np.where(d["short_signal"], supply_high, np.nan))
    d["tsf_structure_target"] = np.where(d["long_signal"], recent_high, np.where(d["short_signal"], recent_low, np.nan))
    return d
