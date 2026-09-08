"""
Triple Screen Trading System — Dr. Alexander Elder ("Trading for a
Living", 1993; refined in "Come Into My Trading Room"). No source
document or video was provided for this one — confirmed with the user
before building — so this is built from the well-documented, widely-
taught standard version of the system, not a transcription of a
specific text. Flagged explicitly since this project's practice
elsewhere has been to build from a verbatim source; here the "source"
is the strategy's own broadly-published, standardized description.

**Screen 1 (long-term "tide", weekly)** — direction only, never itself
an entry trigger. Elder's own indicator choice: the WEEKLY MACD-
Histogram's SLOPE — rising = bullish tide (only look for longs), falling
= bearish tide (only look for shorts). Specifically the slope, not the
MACD/signal-line cross and not the histogram's sign — Elder's own
emphasis is that a rising histogram (even a negative one recovering
toward zero) already signals improving upside momentum, before a
crossover would confirm it.

**Screen 2 (intermediate "wave", daily)** — Force Index(2)
(`engines/force_index.py`, Elder's own indicator, and his stated
preference for Triple Screen specifically over Stochastic, his other
suggested option) dipping AGAINST the tide (negative during a bullish
tide, positive during a bearish one) identifies a pullback offering a
favorable entry price. Treated as an "armed" state valid for a short
window (`timing_window`, default 3 bars), not a same-bar-only
condition — Elder's own method is to leave a resting stop order active
for a day or two waiting for Screen 3 to trigger it. Same "arm on
condition A within a recent window, trigger on condition B same day"
composition already used by `strategies/mama.py` elsewhere in this
project (`bars_since(...) <= window`).

**Screen 3 (short-term "ripple", daily close)** — Elder's actual method
places a resting buy-stop just above the last 2 days' high (an intrabar
order). This project's backtest engine only fills close-based signals
at the next bar's open (see `backtest/engine.py`'s own no-lookahead
discipline, applied consistently across every strategy here, none of
which simulate true intrabar stop orders) — adapted as a CLOSE breaking
above the 2-day high, reusing `price_action.py`'s already-tested
`breakout_level_up`/`is_breakout_up` rather than a new primitive.

**Exit**: Elder's own text discusses several trailing-stop approaches
(a moving average, channel lines, the SafeZone system) without one
single crisp numeric rule — the same kind of gap this project has
handled for every other book/deck source without an unambiguous exit
(e.g. `support_20pct.py`). Used here: a structural stop just beyond the
OTHER side of the Screen-3 breakout window (the level whose breach
would itself invalidate the setup) with the usual ATR floor, and this
project's standard 2R fixed target — a reasonable, flagged default, not
a literal transcription of Elder's own (more open-ended) guidance.
"""

import pandas as pd

from cryptobot.engines.macd import macd, DEFAULT_FAST as DEFAULT_MACD_FAST, DEFAULT_SLOW as DEFAULT_MACD_SLOW, \
    DEFAULT_SIGNAL as DEFAULT_MACD_SIGNAL
from cryptobot.engines.force_index import force_index, DEFAULT_SMOOTHING as DEFAULT_FORCE_INDEX_SMOOTHING
from cryptobot.engines.price_action import breakout_level_up, breakout_level_down, is_breakout_up, is_breakout_down
from cryptobot.engines.multi_timeframe import merge_higher_timeframe_series
from cryptobot.utils import bars_since

DEFAULT_BREAKOUT_LOOKBACK = 2
DEFAULT_TIMING_WINDOW = 3


def compute_triple_screen(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                           macd_fast: int = DEFAULT_MACD_FAST, macd_slow: int = DEFAULT_MACD_SLOW,
                           macd_signal: int = DEFAULT_MACD_SIGNAL,
                           force_index_smoothing: int = DEFAULT_FORCE_INDEX_SMOOTHING,
                           breakout_lookback: int = DEFAULT_BREAKOUT_LOOKBACK,
                           timing_window: int = DEFAULT_TIMING_WINDOW) -> pd.DataFrame:
    d = daily_df.copy()

    # Screen 1: weekly MACD-histogram slope, merged onto daily.
    _, _, weekly_hist = macd(weekly_df["close"], macd_fast, macd_slow, macd_signal)
    weekly_hist_known = weekly_hist.notna() & weekly_hist.shift(1).notna()
    weekly_hist_rising = (weekly_hist > weekly_hist.shift(1)) & weekly_hist_known

    tide_known = merge_higher_timeframe_series(d, weekly_df, weekly_hist_known, "1w").fillna(False).astype(bool)
    tide_rising = merge_higher_timeframe_series(d, weekly_df, weekly_hist_rising, "1w").fillna(False).astype(bool)
    tide_bullish = tide_rising & tide_known
    tide_bearish = (~tide_rising) & tide_known

    # Screen 2: daily Force Index(2) against the tide.
    fi = force_index(d, force_index_smoothing)
    pullback_long = tide_bullish & (fi < 0)
    pullback_short = tide_bearish & (fi > 0)

    # Screen 3: close breaks the N-day high/low - the entry trigger.
    breakout_up = is_breakout_up(d, breakout_lookback)
    breakout_down = is_breakout_down(d, breakout_lookback)

    d["ts_tide_bullish"] = tide_bullish
    d["ts_tide_bearish"] = tide_bearish
    d["ts_force_index"] = fi
    d["ts_pullback_long"] = pullback_long
    d["ts_pullback_short"] = pullback_short
    d["long_signal"] = tide_bullish & (bars_since(pullback_long) <= timing_window) & breakout_up
    d["short_signal"] = tide_bearish & (bars_since(pullback_short) <= timing_window) & breakout_down

    # Structural stop: the far side of the Screen-3 breakout window -
    # the level whose breach invalidates the setup, per Elder's own
    # "protective stop just below/above the recent minor low/high".
    d["ts_structure_stop"] = pd.Series(
        breakout_level_down(d, breakout_lookback).where(d["long_signal"])
    ).combine_first(breakout_level_up(d, breakout_lookback).where(d["short_signal"]))
    return d
