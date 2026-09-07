"""
Bebemon (Bollinger Band Monster) — SPYFRAT deck's "Trading Hacks" section.

*** IMPORTANT: this is NOT a transcription of the deck's actual rule. ***
The deck describes Bebemon only in visual/discretionary terms: "a price
transition around or above the 50-period moving average that looks like
a duckbill... can be traded two ways: a) around the 50-prd MA or as the
bill is being formed, or b) on the pattern breakout," with no numeric
definition given anywhere in the source, and explicitly listed as
covering seven different discretionary setup types (bottom play,
reversal, trend following, momo, pattern formation, breakouts,
parabolics). Built anyway per explicit user request, with this caveat
stated up front: what's tested below is THIS module's own operational
interpretation of "duckbill consolidation near the 50-MA, then breakout,"
not "Segovia's Bebemon" as he would trade it discretionarily. A different
interpretation could produce materially different results.

Interpretation: price consolidates INSIDE the tight custom Bollinger(50,
0.20) envelope (the same band defined for the SPYFRAT core system, since
the deck explicitly ties Bebemon to that same "Bollinger Band Monster")
for several consecutive bars — the "duckbill" — followed by a breakout
above the upper band with volume confirmation.

Exit: stop below the 50-period MA, per the deck's own explicit
instruction for breakout traders ("Stop loss placement below the 50-prd
MA... for breakout traders") — a real instruction from the source, unlike
the entry geometry above.
"""

import pandas as pd

from cryptobot.engines.moving_averages import bollinger_bands
from cryptobot.engines.volume import is_volume_expansion, DEFAULT_LOOKBACK, DEFAULT_EXPANSION_THRESHOLD

DEFAULT_BB_LENGTH = 50
DEFAULT_BB_STD = 0.20
DEFAULT_CONSOLIDATION_BARS = 5


def compute_bebemon(df: pd.DataFrame, bb_length: int = DEFAULT_BB_LENGTH, bb_std: float = DEFAULT_BB_STD,
                     consolidation_bars: int = DEFAULT_CONSOLIDATION_BARS,
                     volume_lookback: int = DEFAULT_LOOKBACK,
                     volume_threshold: float = DEFAULT_EXPANSION_THRESHOLD) -> pd.DataFrame:
    d = df.copy()
    basis, upper, lower = bollinger_bands(d["close"], bb_length, bb_std)
    d["bebemon_basis"] = basis
    d["bebemon_upper"] = upper
    d["bebemon_lower"] = lower

    inside_band = (d["close"] <= upper) & (d["close"] >= lower)
    prior_inside = inside_band.shift(1).fillna(False).astype(int)
    was_consolidating = prior_inside.rolling(consolidation_bars).sum() == consolidation_bars

    breakout = (d["close"] > upper) & (d["close"].shift(1) <= upper.shift(1))
    volume_confirm = is_volume_expansion(d, volume_lookback, volume_threshold)

    d["bebemon_was_consolidating"] = was_consolidating.fillna(False)
    d["long_signal"] = d["bebemon_was_consolidating"] & breakout.fillna(False) & volume_confirm
    return d
