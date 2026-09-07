"""
CALMA (CCI + ALMA) — "The Forbidden Book" Strategy 3 of 7.

Book's exact rules (Weekly timeframe — "suited sa mga traders na di
gaanong nakakababad sa market... once a week lang natingin"):
  Buy: CCI crosses up through +100 AND candle above ALMA.
  Exit: candle breaks below ALMA and stays below (trailing_indicator).

Long-only (see mama.py's module docstring for why).
"""

import pandas as pd

from cryptobot.engines.moving_averages import (
    alma, DEFAULT_ALMA_WINDOW, DEFAULT_ALMA_OFFSET, DEFAULT_ALMA_SIGMA,
)
from cryptobot.engines.oscillators import cci, DEFAULT_CCI_LENGTH

DEFAULT_CCI_THRESHOLD = 100


def compute_calma(df: pd.DataFrame, alma_window: int = DEFAULT_ALMA_WINDOW,
                   alma_offset: float = DEFAULT_ALMA_OFFSET, alma_sigma: float = DEFAULT_ALMA_SIGMA,
                   cci_length: int = DEFAULT_CCI_LENGTH, cci_threshold: float = DEFAULT_CCI_THRESHOLD) -> pd.DataFrame:
    d = df.copy()
    d["calma_alma"] = alma(d["close"], alma_window, alma_offset, alma_sigma)
    c = cci(d, cci_length)
    d["calma_cci"] = c

    cci_cross_up = (c >= cci_threshold) & (c.shift(1) < cci_threshold)
    above_alma = d["close"] > d["calma_alma"]
    d["long_signal"] = cci_cross_up.fillna(False) & above_alma
    return d
