"""Small helpers shared across engines. Kept here (not duplicated per
module) specifically because copy-pasting this exact kind of helper
across files is the pattern the Phase 1 audit flagged in the original 7
standalone bots — not repeating it in the new package."""

import numpy as np
import pandas as pd


def bars_since(cond: pd.Series) -> pd.Series:
    """Bars since `cond` was last True (0 on the bar it's True itself);
    a large number if never true yet. Backward-only by construction:
    forward-fills the row index where True, using only past/current
    rows, then subtracts — never references a later row."""
    idx = np.arange(len(cond))
    last_true_idx = np.where(cond.values, idx, np.nan)
    last_true_idx = pd.Series(last_true_idx, index=cond.index).ffill()
    return pd.Series(idx, index=cond.index) - last_true_idx
