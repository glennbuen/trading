"""
20% Rule — Support Bounce, from the SPYFRAT deck's "Trading Hacks"
section ("Using the 20 Percent Rule as Major Support").

Deck's exact rule: "Major support from a price high after a 20%
correction... The first 20 percent correction will normally have a
bounce (average bounce 5 to 7 percent); an overshoot is common but still
has high success rate for a bounce. But a second test of support will
have a high likelihood of breaking through major support so avoid."

Support level = confirmed swing high (market_structure.resistance) x
0.80. Entry = the FIRST time price ever touches that level (regardless of
outcome — a touch that fails to bounce still "uses up" the one eligible
attempt, per the deck's own caution against a second test) AND that first
touch shows a same-bar reclaim (a bounce). No entry ever fires if the
first touch breaks through instead of bouncing — exactly matching "avoid"
the second test, since there IS no second attempt once the first has
failed.

Exit: the deck states an expected magnitude ("average bounce 5 to 7
percent") but no explicit stop/target mechanism for this specific setup —
unlike several of the deck's other rules. A structural stop below the
support level (with the usual ATR floor) plus the standard fixed-R target
convention used throughout this project is the exit model applied here;
it is a reasonable proxy, not a literal transcription of "5 to 7 percent."
"""

import pandas as pd

from cryptobot.engines import market_structure as ms

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_CORRECTION_PCT = 20.0
DEFAULT_TOUCH_TOLERANCE_PCT = 1.0


def compute_support_20pct(df: pd.DataFrame, structure_left: int = DEFAULT_STRUCTURE_LEFT,
                           structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                           correction_pct: float = DEFAULT_CORRECTION_PCT,
                           touch_tolerance_pct: float = DEFAULT_TOUCH_TOLERANCE_PCT) -> pd.DataFrame:
    d = df.copy()
    swing_high = ms.resistance(d, structure_left, structure_right)
    support_level = swing_high * (1 - correction_pct / 100)
    d["s20_swing_high"] = swing_high
    d["s20_support_level"] = support_level

    # A new support level is established each time the underlying swing
    # high (hence support_level) updates to a genuinely new confirmed
    # value — support_level is otherwise constant (ffilled) between
    # updates, so this comparison only flags real new-level events.
    level_episode = (support_level != support_level.shift(1)).cumsum()

    touched_any = (d["low"] <= support_level * (1 + touch_tolerance_pct / 100)) & support_level.notna()
    touch_count_so_far = touched_any.groupby(level_episode).cumsum()
    is_first_touch_ever = touch_count_so_far == 1
    reclaimed = d["close"] > support_level

    d["s20_touched"] = touched_any
    d["long_signal"] = touched_any & is_first_touch_ever & reclaimed.fillna(False)
    return d
