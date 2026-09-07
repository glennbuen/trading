"""
BOPIS — "The Forbidden Book" Strategy 6 of 7. Bottom-fishing setup:
Parabolic SAR + EMA9 + Trix.

Book's exact rules (Daily timeframe):
  Buy: Parabolic SAR dots below the candle AND candle above EMA9 AND Trix
       is about to cross over zero, or has just crossed over zero (a +-1
       bar timing window — same "day before/at/after" convention as
       MAMA's MACD condition, applied here to a single event since only
       one crossing condition is involved, not two independent ones).
  Exit: breakdown of EMA9 as support (candle closes below EMA9 and stays
        below — trailing_indicator).

Parabolic SAR and Trix both use TradingView's default parameters (step=
0.02/max=0.2 for SAR; the book gives Trix=7 explicitly for BOPIS
specifically, unlike FISHBALL's Trix=5).

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.utils import bars_since
from cryptobot.engines.moving_averages import ema
from cryptobot.engines.parabolic_sar import dots_below_price, DEFAULT_STEP, DEFAULT_MAX_AF
from cryptobot.engines.oscillators import trix_cross_up_zero

DEFAULT_EMA_LENGTH = 9
DEFAULT_TRIX_LENGTH = 7  # book's explicit setting for BOPIS specifically
DEFAULT_TIMING_WINDOW = 1


def compute_bopis(df: pd.DataFrame, ema_length: int = DEFAULT_EMA_LENGTH, psar_step: float = DEFAULT_STEP,
                   psar_max_af: float = DEFAULT_MAX_AF, trix_length: int = DEFAULT_TRIX_LENGTH,
                   timing_window: int = DEFAULT_TIMING_WINDOW) -> pd.DataFrame:
    d = df.copy()
    d["bopis_ema9"] = ema(d["close"], ema_length)

    dots_below = dots_below_price(d, psar_step, psar_max_af)
    above_ema = d["close"] > d["bopis_ema9"]
    trix_zero_cross = trix_cross_up_zero(d["close"], trix_length)
    since_trix_cross = bars_since(trix_zero_cross)

    d["bopis_dots_below"] = dots_below
    d["bopis_above_ema9"] = above_ema
    d["bopis_trix_cross_up_zero"] = trix_zero_cross
    d["long_signal"] = dots_below & above_ema & (since_trix_cross <= timing_window)
    return d
