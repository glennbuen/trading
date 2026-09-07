"""
Ceiling / Follow-Through Play — SPYFRAT deck's "Trading Hacks" section
("Using the 20 Percent Rule for Follow-Thru Play").

*** IMPORTANT CAVEAT, stated up front: *** the deck's "ceiling day" refers
to the Philippine Stock Exchange's daily price UP-LIMIT ("ceiling") — a
regulatory circuit-breaker capping how far a stock can rise in one
session. Crypto majors (BTC/ETH on OKX) have NO such mechanic — there is
no daily price cap. This module defines a crypto ANALOG (an extreme
single-day % gain, not an exchange-imposed limit) rather than a faithful
transcription of a rule that depends on market structure crypto doesn't
have. Expected to produce very few — plausibly zero — signals on BTC/ETH
for exactly this reason: majors rarely gain 15%+ in a single day, let
alone twice in a row. That mismatch between the rule's origin market and
crypto is itself the honest finding here, not a bug to route around.

Deck's rule: after a "ceiling day," the follow-through day must open with
a further +20% gain (from the ceiling day's close) to confirm strong
momentum — that open then becomes a new trailing pivot. An open gain
below +20% signals to take profits/slice instead (not implemented as a
separate signal here — only the confirmed-momentum entry is).

Timing note: the deck's rule is about acting AT the follow-through day's
own open. This project's backtest engine only fills at the bar AFTER a
signal is confirmed on a prior bar's CLOSE (see backtest/engine.py's
no-lookahead discipline) — so this fires once the follow-through day has
itself fully closed (its own open is by then historical, known data), and
the actual trade fills one bar later still. An honest consequence of not
trading on a bar that hasn't finished yet, not a shortcut.
"""

import pandas as pd

DEFAULT_CEILING_GAIN_PCT = 15.0  # crypto analog threshold for an "extreme" single-day move
DEFAULT_FOLLOWTHROUGH_GAIN_PCT = 20.0


def compute_ceiling_followthrough(df: pd.DataFrame, ceiling_gain_pct: float = DEFAULT_CEILING_GAIN_PCT,
                                   followthrough_gain_pct: float = DEFAULT_FOLLOWTHROUGH_GAIN_PCT) -> pd.DataFrame:
    d = df.copy()
    daily_gain_pct = (d["close"] / d["close"].shift(1) - 1) * 100
    ceiling_day = daily_gain_pct >= ceiling_gain_pct
    was_ceiling_day = ceiling_day.shift(1).fillna(False).astype(bool)

    # Follow-through day's OWN open vs. the ceiling day's close. At row i
    # (the follow-through day), the ceiling day is row i-1, so its close
    # is close.shift(1) evaluated at row i.
    open_gain_from_ceiling_close_pct = (d["open"] / d["close"].shift(1) - 1) * 100

    d["cf_ceiling_day"] = ceiling_day
    d["cf_daily_gain_pct"] = daily_gain_pct
    d["cf_open_gain_from_ceiling_pct"] = open_gain_from_ceiling_close_pct
    d["long_signal"] = (was_ceiling_day & (open_gain_from_ceiling_close_pct >= followthrough_gain_pct)).fillna(False)
    return d
