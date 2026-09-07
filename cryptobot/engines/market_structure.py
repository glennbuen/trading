"""
Market Structure Engine — deterministic swing points, trend classification,
break of structure, and simple support/resistance.

THE CENTRAL NO-LOOKAHEAD ISSUE IN THIS MODULE, more subtle than anywhere
else in the package: a swing high/low is a FRACTAL pattern — bar i is only
confirmed as a swing high once `right` bars AFTER it have closed without
making a higher high. That means the swing is not knowable until bar
i + right, even though it "happened" at bar i.

This module always exposes two things for a swing: where it happened
(useful for plotting/research) and where it became KNOWABLE (the only
version safe to feed into a live signal or a backtest that must not
cheat). The confirmed/knowable series are produced via `.shift(right)` —
the same backward-only-lag technique already validated in this repo
(okx_orb_trend_bot.py's daily-trend filter). Every trend/BOS/support-
resistance function in this module is built from the CONFIRMED swing
series only, never the raw one, so nothing downstream can accidentally
cheat. See tests/test_market_structure.py for a synthetic-series test
that asserts computing on a truncated prefix reproduces the same output as
computing on the full series, for every row that should be unaffected by
the truncation.
"""

import numpy as np
import pandas as pd

DEFAULT_LEFT = 3
DEFAULT_RIGHT = 3


def swing_high_raw(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    """True at bar i if high[i] is strictly greater than every high in the
    `left` bars before and `right` bars after it. Uses future bars
    internally by design — this is the retrospective pattern, not the
    live-safe one. Use swing_high_confirmed for anything live/backtest."""
    high = df["high"]
    is_max = pd.Series(True, index=df.index)
    for k in range(1, left + 1):
        is_max &= high > high.shift(k)
    for k in range(1, right + 1):
        is_max &= high > high.shift(-k)
    return is_max.fillna(False)


def swing_low_raw(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    low = df["low"]
    is_min = pd.Series(True, index=df.index)
    for k in range(1, left + 1):
        is_min &= low < low.shift(k)
    for k in range(1, right + 1):
        is_min &= low < low.shift(-k)
    return is_min.fillna(False)


def swing_high_confirmed(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                          right: int = DEFAULT_RIGHT) -> pd.Series:
    """True at bar i+right, the first bar where the swing at bar i is
    actually knowable. This is the live/backtest-safe version."""
    raw = swing_high_raw(df, left, right)
    return raw.shift(right).fillna(False).astype(bool)


def swing_low_confirmed(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                         right: int = DEFAULT_RIGHT) -> pd.Series:
    raw = swing_low_raw(df, left, right)
    return raw.shift(right).fillna(False).astype(bool)


def swing_high_confirmed_value(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                                right: int = DEFAULT_RIGHT) -> pd.Series:
    """The swing high's price, placed at the bar where it becomes
    knowable (not at the bar where the peak actually occurred)."""
    confirmed = swing_high_confirmed(df, left, right)
    return df["high"].shift(right).where(confirmed)


def swing_low_confirmed_value(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                               right: int = DEFAULT_RIGHT) -> pd.Series:
    confirmed = swing_low_confirmed(df, left, right)
    return df["low"].shift(right).where(confirmed)


def last_confirmed_value(value_at_confirmation: pd.Series) -> pd.Series:
    """Forward-fill a sparse 'value at the bar it's confirmed' series so
    every bar sees the latest confirmed value. Backward-only by
    construction (ffill never uses a future row)."""
    return value_at_confirmation.ffill()


def prior_confirmed_value(value_at_confirmation: pd.Series) -> pd.Series:
    """The confirmed value from ONE confirmation before the latest, i.e.
    what the level was before its most recent update. Used to classify
    higher-high/lower-low style comparisons."""
    compact = value_at_confirmation.dropna()
    prior = compact.shift(1)
    full = pd.Series(np.nan, index=value_at_confirmation.index)
    full.loc[prior.index] = prior.values
    return full.ffill()


def resistance(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    """Most recent confirmed swing high, as of each bar — a simple
    support/resistance baseline. The liquidity engine (Phase 3) builds
    equal-highs/sweeps detection on top of this."""
    return last_confirmed_value(swing_high_confirmed_value(df, left, right))


def support(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    return last_confirmed_value(swing_low_confirmed_value(df, left, right))


def higher_high(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    """True exactly on the bar a new confirmed swing high prints higher
    than the previous confirmed swing high (an event, not a standing
    state)."""
    conf_val = swing_high_confirmed_value(df, left, right)
    prior = prior_confirmed_value(conf_val)
    return (conf_val.notna() & prior.notna() & (conf_val > prior))


def lower_high(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    conf_val = swing_high_confirmed_value(df, left, right)
    prior = prior_confirmed_value(conf_val)
    return (conf_val.notna() & prior.notna() & (conf_val < prior))


def higher_low(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    conf_val = swing_low_confirmed_value(df, left, right)
    prior = prior_confirmed_value(conf_val)
    return (conf_val.notna() & prior.notna() & (conf_val > prior))


def lower_low(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    conf_val = swing_low_confirmed_value(df, left, right)
    prior = prior_confirmed_value(conf_val)
    return (conf_val.notna() & prior.notna() & (conf_val < prior))


def trend_state(df: pd.DataFrame, left: int = DEFAULT_LEFT, right: int = DEFAULT_RIGHT) -> pd.Series:
    """
    'up'   — most recent swing-high event was a higher-high AND most
             recent swing-low event was a higher-low.
    'down' — most recent swing-high event was a lower-high AND most
             recent swing-low event was a lower-low.
    'transition' — the two disagree (classic BOS/CHoCH precursor).
    'undefined' — not enough confirmed swings yet.
    Persisted forward (ffill) between events, same backward-only rule as
    everything else here.
    """
    hh = higher_high(df, left, right)
    lh = lower_high(df, left, right)
    hl = higher_low(df, left, right)
    ll = lower_low(df, left, right)

    high_call = pd.Series(np.where(hh, "higher", np.where(lh, "lower", None)), index=df.index)
    low_call = pd.Series(np.where(hl, "higher", np.where(ll, "lower", None)), index=df.index)
    high_call = high_call.ffill()
    low_call = low_call.ffill()

    state = pd.Series("undefined", index=df.index)
    state[(high_call == "higher") & (low_call == "higher")] = "up"
    state[(high_call == "lower") & (low_call == "lower")] = "down"
    both_known = high_call.notna() & low_call.notna()
    undecided = both_known & ~(state.isin(["up", "down"]))
    state[undecided] = "transition"
    return state


def break_of_structure_up(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                           right: int = DEFAULT_RIGHT) -> pd.Series:
    """Edge-triggered: close crosses above the most recent confirmed
    swing high (the level was known as of the PRIOR bar, so this doesn't
    use the current bar's own high/low to define the level it's testing
    against)."""
    level = resistance(df, left, right).shift(1)
    return (df["close"] > level) & (df["close"].shift(1) <= level.shift(1))


def break_of_structure_down(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                             right: int = DEFAULT_RIGHT) -> pd.Series:
    level = support(df, left, right).shift(1)
    return (df["close"] < level) & (df["close"].shift(1) >= level.shift(1))


def previous_day_levels(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Previous COMPLETE UTC day's high/low, mapped onto every bar of the
    current day. No lookahead: only a fully-closed prior day is used
    (same pattern as okx_vwap_pivot_bot.py's pivot calculation)."""
    d = df.copy()
    d["_date"] = d["dt"].dt.date
    daily = d.groupby("_date").agg(day_high=("high", "max"), day_low=("low", "min")).reset_index()
    daily = daily.sort_values("_date").reset_index(drop=True)
    daily[["day_high", "day_low"]] = daily[["day_high", "day_low"]].shift(1)
    merged = d.merge(daily, on="_date", how="left")
    return merged["day_high"], merged["day_low"]


def compute_market_structure(df: pd.DataFrame, left: int = DEFAULT_LEFT,
                              right: int = DEFAULT_RIGHT) -> pd.DataFrame:
    """Convenience: compute every market-structure column at once."""
    d = df.copy()
    d["ms_swing_high_confirmed"] = swing_high_confirmed(d, left, right)
    d["ms_swing_low_confirmed"] = swing_low_confirmed(d, left, right)
    d["ms_resistance"] = resistance(d, left, right)
    d["ms_support"] = support(d, left, right)
    d["ms_higher_high"] = higher_high(d, left, right)
    d["ms_lower_high"] = lower_high(d, left, right)
    d["ms_higher_low"] = higher_low(d, left, right)
    d["ms_lower_low"] = lower_low(d, left, right)
    d["ms_trend_state"] = trend_state(d, left, right)
    d["ms_bos_up"] = break_of_structure_up(d, left, right)
    d["ms_bos_down"] = break_of_structure_down(d, left, right)
    d["ms_prev_day_high"], d["ms_prev_day_low"] = previous_day_levels(d)
    return d
