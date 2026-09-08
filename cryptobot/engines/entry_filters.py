"""
Entry Filters Engine — generic, reusable price-location filters,
composable onto ANY strategy's entry signal. Built for a "near/within
striking distance of EMA(10)" retest requested across every strategy in
this project — confirmed with the user before building: % distance from
close to EMA(N) (not ATR-based), price required on the FAVORABLE side (a
pullback into value, not mere proximity in either direction) — for a
long, close at or below the EMA but within the threshold; the mirror for
a short.

Two distinct compositions, requested in two separate rounds — do not
conflate them:

1. `near_ema_pullback()` — a SAME-BAR AND filter: the strategy's own
   entry signal must fire on a bar where price also happens to be near
   the EMA. First retest run this way
   (`docs/EVALUATION_EMA10_FILTER_RETEST.md`) — found this crushes
   breakout-style entries to zero trades, since a genuine breakout tends
   to happen when price is EXTENDED away from a short EMA, not pulled
   back near one; same-bar coincidence of "just broke out" and "near the
   EMA" is close to a contradiction for that entry style.

2. `pullback_entry_after_breakout()` — the corrected, SEQUENTIAL
   composition: the strategy's own entry signal is reinterpreted as an
   ARMING event (a breakout occurred), not the entry itself. The actual
   entry fires on the FIRST bar, within an `arming_window` of bars AFTER
   that breakout, where price has pulled back near the EMA — "entry is
   after breakout, buy at the pullback around EMA(10)", the user's own
   phrasing for the corrected version. This is the version actually
   evaluated in `docs/EVALUATION_EMA10_PULLBACK_AFTER_BREAKOUT.md`.
"""

import pandas as pd

from cryptobot.engines.moving_averages import ema
from cryptobot.utils import bars_since

DEFAULT_EMA_PERIOD = 10
DEFAULT_MAX_DISTANCE_PCT = 2.0
DEFAULT_ARMING_WINDOW = 10


def near_ema_pullback(df: pd.DataFrame, ema_period: int = DEFAULT_EMA_PERIOD,
                       max_distance_pct: float = DEFAULT_MAX_DISTANCE_PCT) -> tuple:
    """Returns (near_long, near_short).
    near_long: close is AT OR BELOW the EMA (a pullback into value, the
      favorable side for a long entry) AND within max_distance_pct of it.
    near_short: the mirror — close at or above the EMA, within
      max_distance_pct."""
    e = ema(df["close"], ema_period)
    dist_pct = (df["close"] - e).abs() / e.replace(0, pd.NA) * 100
    near_long = (df["close"] <= e) & (dist_pct <= max_distance_pct)
    near_short = (df["close"] >= e) & (dist_pct <= max_distance_pct)
    return near_long.fillna(False), near_short.fillna(False)


def compute_entry_filters(df: pd.DataFrame, ema_period: int = DEFAULT_EMA_PERIOD,
                           max_distance_pct: float = DEFAULT_MAX_DISTANCE_PCT) -> pd.DataFrame:
    d = df.copy()
    d["ef_ema"] = ema(d["close"], ema_period)
    d["ef_near_ema_long"], d["ef_near_ema_short"] = near_ema_pullback(d, ema_period, max_distance_pct)
    return d


def pullback_entry_after_breakout(breakout_event: pd.Series, near_ema_side: pd.Series,
                                   arming_window: int = DEFAULT_ARMING_WINDOW) -> pd.Series:
    """The actual entry trigger: the FIRST bar within `arming_window`
    bars after a `breakout_event` (the strategy's own original entry
    signal, reinterpreted as an arming event — "a breakout occurred, now
    watch for the pullback") where `near_ema_side` (near_long or
    near_short from near_ema_pullback, matching the breakout's own
    direction) is true. Fires at most once per breakout — a NEW breakout
    is required to arm a fresh watch, not every touch within the window
    of the same breakout.

    `arming_window` (default 10 bars) is a chosen default, not specified
    by the user's own phrasing — flagged explicitly, same as every other
    unspecified numeric choice in this project. Long enough to give a
    genuine pullback time to develop (longer than the 3-bar "resting
    stop order" windows used elsewhere in this project for a same-
    direction re-trigger, e.g. mama.py/triple_screen.py, since this is
    about waiting for a retracement after a full breakout move, not a
    tight order-timing window)."""
    episode_id = breakout_event.cumsum()
    in_window = bars_since(breakout_event) <= arming_window
    touch = in_window & near_ema_side
    touch_count = touch.groupby(episode_id).cumsum()
    return touch & (touch_count == 1)
