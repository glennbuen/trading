"""
DAY TRADING (ALMA only) — "The Forbidden Book" Strategy 7 of 7, and the
simplest: pure ALMA breakout/breakdown, no other indicator.

Book's exact rules: "Buy signal is kapag na break ang ALMA as resistance
at sell is kapag nabreak ang ALMA as support." 1-15 minute timeframe; the
book itself recommends switching from 1m to 15m in practice ("Use ALMA
and switch ka mula 1 min Timeframe to 15 Minute Timeframe") — 15m used
here for evaluation.

The book states two "non-negotiable" risk rules alongside this strategy:
use only 10% of account equity for day trading, and respect exits without
debate. The position-sizing rule is a RiskLimits.max_position_pct=10
choice made when evaluating this strategy (a risk-config concern), not
hardcoded into the signal logic here. "Respect exits" is exactly what the
backtest engine's trailing_indicator method already enforces mechanically
— it doesn't skip an exit signal.

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.engines.moving_averages import (
    alma, DEFAULT_ALMA_WINDOW, DEFAULT_ALMA_OFFSET, DEFAULT_ALMA_SIGMA,
)


def compute_day_trading_alma(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                              alma_offset: float = DEFAULT_ALMA_OFFSET,
                              alma_sigma: float = DEFAULT_ALMA_SIGMA) -> pd.DataFrame:
    d = df.copy()
    d["dt_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)
    above = d["close"] > d["dt_alma"]
    was_above = above.shift(1).fillna(False).astype(bool)
    d["long_signal"] = above & ~was_above
    return d
