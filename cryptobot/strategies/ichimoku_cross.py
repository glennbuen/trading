"""
Ichimoku Cross Strategy — the classic "full system" Ichimoku signal, built
on cryptobot/engines/ichimoku.py.

A genuinely different hypothesis from this project's 4 spec strategies,
which all compose price_action/market_structure/volume/liquidity —
already tested exhaustively (Strategy Comparison, docs/STRATEGY_COMPARISON.md)
with no validated edge found among them. Ichimoku is tested here entirely
on its own terms, faithful to the classic textbook signal rather than
augmented with this project's other engines — the point is to give the
indicator itself a fair, unmodified test.

Entry requires ALL FOUR classic conditions to agree (per spec §15: no
single indicator/condition should trigger a trade alone — here all four
belong to one system, but the system itself is only considered "aligned"
when every leg agrees, same discipline as this project's other
strategies):
  1. Tenkan/Kijun cross in the trade's direction (the timing trigger)
  2. Price is on the correct side of the CURRENT cloud (trend filter)
  3. The PROJECTED cloud (not yet displaced) agrees with the direction
     (forward-looking confirmation the trend has room to continue)
  4. Chikou Span confirms (today's close vs. the close `displacement`
     bars ago agrees with the direction)

Exit: Kijun-sen as a structural stop (classic Ichimoku money management —
"stop below Kijun for longs"), via the backtest engine's `method=
"structure"` stop option, with the usual ATR floor as a safety minimum
for degenerate cases where price sits very close to Kijun. Target: fixed
R-multiple, same as this project's other strategies, for direct
comparability.

No lookahead: every column consumed here is already lookahead-safe in
ichimoku.py (see that module's docstring on the cloud-displacement trap
specifically) — this module adds no new temporal decisions, only an AND
of already-safe columns.
"""

import pandas as pd

from cryptobot.engines import ichimoku as ichi

DEFAULT_TENKAN_PERIOD = ichi.DEFAULT_TENKAN_PERIOD
DEFAULT_KIJUN_PERIOD = ichi.DEFAULT_KIJUN_PERIOD
DEFAULT_SENKOU_B_PERIOD = ichi.DEFAULT_SENKOU_B_PERIOD
DEFAULT_DISPLACEMENT = ichi.DEFAULT_DISPLACEMENT


def compute_ichimoku_cross(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                            kijun_period: int = DEFAULT_KIJUN_PERIOD,
                            senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD,
                            displacement: int = DEFAULT_DISPLACEMENT) -> pd.DataFrame:
    d = ichi.compute_ichimoku(df, tenkan_period, kijun_period, senkou_b_period, displacement)

    d["long_signal"] = (d["ichi_tk_cross_up"] & d["ichi_price_above_cloud"] &
                        d["ichi_future_cloud_bullish"] & d["ichi_chikou_bullish"])
    d["short_signal"] = (d["ichi_tk_cross_down"] & d["ichi_price_below_cloud"] &
                         d["ichi_future_cloud_bearish"] & d["ichi_chikou_bearish"])
    # Kijun-sen doubles as the structural stop reference for the backtest
    # engine's method="structure" option.
    d["ichi_kijun_stop"] = d["ichi_kijun"]
    return d
