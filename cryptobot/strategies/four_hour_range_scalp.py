"""
"4-Hour Range" scalping strategy — from the user's own transcript of a
YouTube video (no strategy name given in the video; named here after its
own core mechanic). "No indicators or long preparations... completely
rule-based... a simple three-step checklist."

Only crypto (BTC/USDT, ETH/USDT via OKX) is tested here, even though the
video also demonstrates forex and gold — this project's data source is
OKX, which doesn't offer those markets; consistent with every other
strategy in this project being evaluated only on the symbols this
project's data pipeline actually covers, regardless of what markets a
source video demonstrates.

Step 1 — The range: `engines/session_range.py`'s NY-timezone-anchored
opening range (the high/low of each NY calendar day's first 4 hours,
usable from the moment that window closes through the rest of that NY
day — see that module's docstring for why the timezone handling is done
carefully rather than using OKX's raw UTC-aligned 4h candles, which
would silently mark a different window than the video describes).

Step 2 — The setup: a 5-minute candle must fully CLOSE outside the
range (a wick alone doesn't count — implemented as a close-based edge
trigger, `breakout_up_event`/`breakout_down_event`), then a LATER
5-minute candle must close back inside it, same NY day (automatically
enforced: the range itself goes NaN at the NY midnight boundary, so a
breakout that never re-enters before day-end can never satisfy the
reentry condition — no separate "same day" check needed). Multiple
independent setups on the same day are all valid, matching the video's
own "as long as we're still within the same trading day... we can still
take more trades if another valid setup shows up" — implemented as a
repeatable edge-triggered episode (`breakout_up_event.cumsum()`), not a
first-touch-only gate like several other strategies in this project.

Step 3 — Entry: breakout-up-then-reentry -> short; breakout-down-then-
reentry -> long (a fade of the failed breakout, the video's own logic).
Stop = "the exact high/low of the breakout move" — implemented as the
running max high (for a short) / min low (for a long) reached at any
point DURING that specific excursion outside the range, tracked via the
same episode-scan technique used elsewhere in this project
(`groupby(episode).cummax()`, masked to only accumulate while price is
actually outside the range so it doesn't keep growing during unrelated
later bars in the same episode number). Take-profit = 2x the stop
distance — the video's own explicit rule, and already this project's
existing default (`target_r_multiple=2.0`), so no new backtest-engine
capability was needed for this strategy (unlike `three_step_formula.py`,
which needed a real structural target).

The video's own discretionary exception ("if the breakout was too large,
I looked for the nearest key level instead of the exact high/low") is
NOT implemented — it's explicitly acknowledged as a subjective,
per-chart judgment call in the video itself, not a rule with a stated
numeric trigger, so this module always uses the literal excursion
extreme. Flagged here rather than silently ignored.
"""

import pandas as pd

from cryptobot.engines.session_range import compute_session_range, DEFAULT_HOURS, DEFAULT_TZ


def compute_four_hour_range_scalp(df: pd.DataFrame, hours: int = DEFAULT_HOURS,
                                   tz: str = DEFAULT_TZ) -> pd.DataFrame:
    d = df.copy()
    range_high, range_low = compute_session_range(d, hours, tz)
    d["fhr_range_high"] = range_high
    d["fhr_range_low"] = range_low

    close = d["close"]
    close_prev = close.shift(1)
    range_high_prev = range_high.shift(1)
    range_low_prev = range_low.shift(1)

    breakout_up_event = (close > range_high) & (close_prev <= range_high_prev) & range_high.notna()
    breakout_down_event = (close < range_low) & (close_prev >= range_low_prev) & range_low.notna()

    up_episode = breakout_up_event.cumsum()
    down_episode = breakout_down_event.cumsum()

    outside_up = close > range_high
    outside_down = close < range_low

    # cummax/cummin leave the row ITSELF as NaN wherever the input was
    # masked to NaN (they don't carry the running value forward onto
    # that exact row, only into later non-NaN rows) — so at the reentry
    # bar (outside==False there by definition), the masked cummax/cummin
    # would show NaN right when it's needed. .ffill() recovers the last
    # known excursion extreme at that bar, which is the actual value
    # this module reads at signal time.
    excursion_high = d["high"].where(outside_up).groupby(up_episode).cummax().ffill()
    excursion_low = d["low"].where(outside_down).groupby(down_episode).cummin().ffill()

    reentry_from_up = (close <= range_high) & (close_prev > range_high_prev) & (up_episode > 0) & range_high.notna()
    reentry_from_down = (close >= range_low) & (close_prev < range_low_prev) & (down_episode > 0) & range_low.notna()

    d["fhr_breakout_up_event"] = breakout_up_event
    d["fhr_breakout_down_event"] = breakout_down_event
    d["short_signal"] = reentry_from_up.fillna(False)
    d["long_signal"] = reentry_from_down.fillna(False)

    d["fhr_structure_stop"] = excursion_high.where(d["short_signal"]).combine_first(
        excursion_low.where(d["long_signal"]))
    return d
