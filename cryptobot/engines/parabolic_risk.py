"""
Parabolic Risk Engine — from Hernan Segovia's ("SPYFRAT") Parabolic
Framework, Investagrams Traders' Summit 2018 ("Parabolic Framework and
Trading Hacks", BOH Society).

Deck's exact definitions:
    Parabolic  — RSI(30) > 70 on a given timeframe.
    PHR   (Parabolic High Risk)         — daily RSI(30) > 70 AND weekly
                                            RSI(30) > 70 AND daily > weekly.
                                            "Call to Action: Slice up and
                                            trail stop."
    ePHR  (Extreme Parabolic High Risk) — daily RSI(30) > 80 AND weekly
                                            RSI(30) > 80.
                                            "Call to Action: Sell on sight."

A genuinely multi-timeframe classification — needs both the daily RSI and
the WEEKLY RSI available on every daily bar. Same no-lookahead technique
already validated in this project's earlier standalone bots and
okx_trend_bot.py's MTF mode: a weekly candle opening at T covers [T, T+1w)
and isn't knowable until T+1w closes. `merge_weekly_rsi_onto_daily` tags
each weekly RSI reading with `available_at = ts + 1 week` and
merge_asof(direction="backward")s it onto the daily series, so a daily bar
only ever sees a weekly RSI value from a week that had actually finished
printing by that point.

PHR's "slice up and trail stop" is a position-SCALING instruction (a
partial-profit-then-trail action), which this project's backtest engine
doesn't support (single all-or-nothing position tracking — see
backtest/engine.py's KNOWN LIMITATION note). PHR is exposed here as a
classification column for the strategy layer to use as context/journaling,
not wired into any entry/exit trigger — only ePHR's crisp binary
"sell on sight" instruction is enforceable exactly as stated.
"""

import pandas as pd

from cryptobot.data.exchange import timeframe_to_ms
from cryptobot.engines.oscillators import rsi, DEFAULT_RSI_LENGTH

DEFAULT_PARABOLIC_RSI_LENGTH = 30  # the deck's own setting, not the usual 14
DEFAULT_PARABOLIC_THRESHOLD = 70
DEFAULT_EXTREME_THRESHOLD = 80


def merge_weekly_rsi_onto_daily(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                                 rsi_length: int = DEFAULT_PARABOLIC_RSI_LENGTH) -> pd.Series:
    """Returns the weekly RSI(rsi_length) series aligned onto daily_df's
    index, using only weekly candles that had fully closed by each daily
    bar's timestamp."""
    weekly_rsi = rsi(weekly_df["close"], rsi_length)
    tagged = pd.DataFrame({
        "available_at": weekly_df["ts"] + timeframe_to_ms("1w"),
        "weekly_rsi": weekly_rsi,
    }).sort_values("available_at").reset_index(drop=True)

    daily_sorted = daily_df[["ts"]].sort_values("ts").reset_index(drop=True)
    merged = pd.merge_asof(daily_sorted, tagged, left_on="ts", right_on="available_at",
                            direction="backward")
    merged.index = daily_df.sort_values("ts").index
    return merged["weekly_rsi"].reindex(daily_df.index)


def is_parabolic(rsi_series: pd.Series, threshold: float = DEFAULT_PARABOLIC_THRESHOLD) -> pd.Series:
    return rsi_series > threshold


def is_phr(daily_rsi: pd.Series, weekly_rsi: pd.Series,
           threshold: float = DEFAULT_PARABOLIC_THRESHOLD) -> pd.Series:
    return (daily_rsi > threshold) & (weekly_rsi > threshold) & (daily_rsi > weekly_rsi)


def is_ephr(daily_rsi: pd.Series, weekly_rsi: pd.Series,
            threshold: float = DEFAULT_EXTREME_THRESHOLD) -> pd.Series:
    return (daily_rsi > threshold) & (weekly_rsi > threshold)


def compute_parabolic_risk(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                            rsi_length: int = DEFAULT_PARABOLIC_RSI_LENGTH,
                            parabolic_threshold: float = DEFAULT_PARABOLIC_THRESHOLD,
                            extreme_threshold: float = DEFAULT_EXTREME_THRESHOLD) -> pd.DataFrame:
    d = daily_df.copy()
    d["pr_daily_rsi30"] = rsi(d["close"], rsi_length)
    d["pr_weekly_rsi30"] = merge_weekly_rsi_onto_daily(d, weekly_df, rsi_length)
    d["pr_parabolic"] = is_parabolic(d["pr_daily_rsi30"], parabolic_threshold)
    d["pr_phr"] = is_phr(d["pr_daily_rsi30"], d["pr_weekly_rsi30"], parabolic_threshold)
    d["pr_ephr"] = is_ephr(d["pr_daily_rsi30"], d["pr_weekly_rsi30"], extreme_threshold)
    return d
