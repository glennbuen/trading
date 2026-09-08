"""
Multi-Timeframe Merge Engine — generalizes the weekly-onto-daily merge
first built for `parabolic_risk.merge_weekly_rsi_onto_daily` (RSI-
specific) into a reusable primitive for ANY higher-timeframe series.
Built for Alexander Elder's Triple Screen system (`strategies/
triple_screen.py`), whose Screen 1 needs a weekly trend read merged onto
daily bars, but not specific to it — any future higher/lower-timeframe
strategy in this project should reuse this rather than rewriting the
merge each time.

Same no-lookahead technique validated repeatedly in this project: a bar
opening at T covering a higher timeframe of duration `tf_ms` isn't
knowable until T+tf_ms closes, so each value is tagged with
`available_at = ts + tf_ms` and merge_asof(direction="backward")'d onto
the lower-timeframe series — a lower-timeframe bar only ever sees a
higher-timeframe value from a period that had actually finished by then.
"""

import pandas as pd

from cryptobot.data.exchange import timeframe_to_ms


def merge_higher_timeframe_series(lower_df: pd.DataFrame, higher_df: pd.DataFrame,
                                   higher_series: pd.Series, higher_timeframe: str) -> pd.Series:
    """Returns `higher_series` (any dtype — bool, float, ...) aligned
    onto lower_df's index, using only higher-timeframe bars that had
    fully closed by each lower-timeframe bar's timestamp. NaN wherever
    no higher-timeframe bar had closed yet."""
    tf_ms = timeframe_to_ms(higher_timeframe)
    tagged = pd.DataFrame({
        "available_at": higher_df["ts"].values + tf_ms,
        "value": higher_series.values,
    }).sort_values("available_at").reset_index(drop=True)

    lower_sorted = lower_df[["ts"]].sort_values("ts").reset_index(drop=True)
    merged = pd.merge_asof(lower_sorted, tagged, left_on="ts", right_on="available_at",
                            direction="backward")
    merged.index = lower_df.sort_values("ts").index
    return merged["value"].reindex(lower_df.index)
