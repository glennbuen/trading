"""
Session Range Engine — a fixed-timezone opening range: the high/low of
the first `hours` hours of each calendar day IN A GIVEN TIMEZONE, usable
starting the instant that opening window closes and expiring at that
timezone's own next midnight. Built for the "4-hour range" YouTube
scalping video (see strategies/four_hour_range_scalp.py) but written
generically (hours/timezone are parameters) since "session opening
range" isn't a concept specific to 4 hours or New York.

Timezone handling matters here in a way it hasn't elsewhere in this
project. The video is explicit and repeats it for emphasis: "go to the
time zone setting... select New York time... this step is very
important because we want the first 4-hour candle to be based
specifically on New York time." A naive implementation using the raw
exchange candle boundaries (OKX's native 4h candles are UTC-aligned:
00:00/04:00/08:00 UTC, not NY-local) would silently mark a DIFFERENT
window than the video describes — this module converts the canonical
UTC `dt` column to the target timezone first and buckets by that
timezone's own calendar day, exactly matching what a trader would see
on TradingView with "New York" selected as the chart timezone
(`America/New_York` correctly follows EST/EDT, unlike a fixed UTC-4/-5
offset).

No-lookahead: the window's high/low is a `groupby(...).transform("max"/
"min")` over ONLY the bars inside that specific completed window for
that specific day — safe for any bar at or after the window closes
(the entire window it's built from is already fully in the past by
then) — and is then masked back to NaN for every bar still INSIDE that
window (including earlier bars of the same window, which technically
already "know" the running max/min of bars before them, but are
deliberately kept NaN anyway since the video's own rule is to wait for
the window's OWN candle boundary to fully close, not intrabar). The
range for day D is unavailable during day D's own opening window,
unavailable for day D+1 until day D+1 forms its own window, and never
carries a stale value across the midnight boundary — precisely the
"same day as the range we marked" constraint the video repeats.
"""

import pandas as pd

DEFAULT_HOURS = 4
DEFAULT_TZ = "America/New_York"


def compute_session_range(df: pd.DataFrame, hours: int = DEFAULT_HOURS,
                           tz: str = DEFAULT_TZ) -> tuple:
    """Returns (range_high, range_low), each aligned to df's index. NaN
    while the opening window is still forming (or hasn't started yet for
    that timezone-day); the window's high/low from the moment it closes
    through the rest of that timezone-day; NaN again once the next
    timezone-day's own window starts forming."""
    local_dt = df["dt"].dt.tz_convert(tz)
    day_id = local_dt.dt.date
    in_window = local_dt.dt.hour < hours

    window_high = df["high"].where(in_window)
    window_low = df["low"].where(in_window)

    day_high = window_high.groupby(day_id).transform("max")
    day_low = window_low.groupby(day_id).transform("min")

    range_high = day_high.where(~in_window)
    range_low = day_low.where(~in_window)
    return range_high, range_low
