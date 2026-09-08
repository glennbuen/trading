"""
1h + 15m Trend Filter — day trading's higher-timeframe trend context,
merged onto a lower entry timeframe (5m, per this package's own design:
"1h and 15m for trend, 5m for entry"). Confirmed with the user before
building: BOTH 1h and 15m must independently agree on direction before
a trend is confirmed — a genuine two-screen trend filter, the same
spirit as `cryptobot.strategies.triple_screen`'s weekly/daily structure,
adapted to intraday timeframes (not "1h sets direction, 15m only times
a pullback", the alternative the user was offered and didn't choose).

Reuses `market_structure.trend_state()` (already-tested, general-
purpose trend classifier: up/down/transition/undefined — already used
directly by `liquidity_sweep_reversal.py` elsewhere in this project)
computed independently on each higher timeframe, merged onto the entry
timeframe via `cryptobot.engines.multi_timeframe.
merge_higher_timeframe_series` (already built/tested for Triple Screen)
— called once per higher timeframe. No new swing-detection or merge
logic — this module only composes two already-tested primitives.
"""

import pandas as pd

from cryptobot.engines import market_structure as ms
from cryptobot.engines.multi_timeframe import merge_higher_timeframe_series

DEFAULT_STRUCTURE_LEFT = ms.DEFAULT_LEFT
DEFAULT_STRUCTURE_RIGHT = ms.DEFAULT_RIGHT
DEFAULT_TF1 = "1h"
DEFAULT_TF2 = "15m"


def compute_trend_filter(entry_df: pd.DataFrame, tf1_df: pd.DataFrame, tf2_df: pd.DataFrame,
                          structure_left: int = DEFAULT_STRUCTURE_LEFT,
                          structure_right: int = DEFAULT_STRUCTURE_RIGHT,
                          tf1_name: str = DEFAULT_TF1, tf2_name: str = DEFAULT_TF2) -> pd.DataFrame:
    """`entry_df` is the lower (entry) timeframe — e.g. 5m; `tf1_df`/
    `tf2_df` are the two higher timeframes (full history, e.g. 1h/15m).
    Adds dt_trend_tf1/dt_trend_tf2 (each "up"/"down"/"transition"/
    "undefined", per market_structure.trend_state's own vocabulary) and
    dt_trend_up/dt_trend_down (both-agree booleans) to a copy of
    entry_df."""
    d = entry_df.copy()
    trend_tf1 = ms.trend_state(tf1_df, structure_left, structure_right)
    trend_tf2 = ms.trend_state(tf2_df, structure_left, structure_right)

    merged_tf1 = merge_higher_timeframe_series(d, tf1_df, trend_tf1, tf1_name)
    merged_tf2 = merge_higher_timeframe_series(d, tf2_df, trend_tf2, tf2_name)

    d["dt_trend_tf1"] = merged_tf1
    d["dt_trend_tf2"] = merged_tf2
    d["dt_trend_up"] = (merged_tf1 == "up") & (merged_tf2 == "up")
    d["dt_trend_down"] = (merged_tf1 == "down") & (merged_tf2 == "down")
    return d
