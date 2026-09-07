"""
SPYFRAT Core Trading System — Hernan Segovia, Investagrams Traders'
Summit 2018 ("Parabolic Framework and Trading Hacks", BOH Society).

Deck's exact rules:
  Entry: "buy and sell crossover signals between price and the custom
         Bband" — price crosses above the custom Bollinger(50, 0.20)
         upper band.
  Exit: price crosses below the lower band, OR the position becomes
        Extreme Parabolic High Risk (ePHR — daily AND weekly RSI(30) both
        > 80): "Sell on sight. Sell when it's easy. Don't wait for the
        stampede." (an OR of two conditions — signal_exit, same reasoning
        as FISHBALL/PAPA in "The Forbidden Book" set).

Requires BOTH a daily and a weekly OHLCV series (genuinely multi-
timeframe — see engines/parabolic_risk.py for the no-lookahead merge).

PHR ("slice up and trail stop") is computed by parabolic_risk.py and
exposed as context but not wired into the exit — a position-scaling
instruction this project's single-position backtest engine can't execute.
"""

import pandas as pd

from cryptobot.engines.moving_averages import bollinger_bands
from cryptobot.engines.parabolic_risk import compute_parabolic_risk

DEFAULT_BB_LENGTH = 50
DEFAULT_BB_STD = 0.20


def bollinger_breakout_up(df: pd.DataFrame, length: int = DEFAULT_BB_LENGTH,
                           num_std: float = DEFAULT_BB_STD) -> pd.Series:
    _, upper, _ = bollinger_bands(df["close"], length, num_std)
    above = df["close"] > upper
    was_above = above.shift(1).fillna(False).astype(bool)
    return above & ~was_above


def compute_spyfrat_system(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                            bb_length: int = DEFAULT_BB_LENGTH, bb_std: float = DEFAULT_BB_STD,
                            parabolic_rsi_length: int = 30, parabolic_threshold: float = 70,
                            extreme_threshold: float = 80) -> pd.DataFrame:
    d = compute_parabolic_risk(daily_df, weekly_df, parabolic_rsi_length,
                                parabolic_threshold, extreme_threshold)
    basis, upper, lower = bollinger_bands(d["close"], bb_length, bb_std)
    d["spyfrat_bb_basis"] = basis
    d["spyfrat_bb_upper"] = upper
    d["spyfrat_bb_lower"] = lower

    d["long_signal"] = bollinger_breakout_up(d, bb_length, bb_std)

    below_lower = d["close"] < lower
    d["spyfrat_exit_signal"] = below_lower.fillna(False) | d["pr_ephr"].fillna(False)
    return d
