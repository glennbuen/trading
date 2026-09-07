"""
Ichimoku Kinko Hyo Engine.

A classic, self-contained Japanese technical system — not composed from
the other engines (price_action/market_structure/volume/liquidity), all
of which this project has already tested exhaustively across 4 strategies
with no validated edge found. Ichimoku is a genuinely different
hypothesis, built and tested on its own terms.

THE LOOKAHEAD TRAP THIS MODULE IS CAREFUL ABOUT: Ichimoku's Senkou spans
are conventionally PLOTTED 26 bars ahead of where they're computed — a
charting convention, not a computation rule. Naively using
`senkou_span_a` (computed from TODAY's Tenkan/Kijun) as "today's cloud"
would be a real lookahead bug: that span isn't meant to describe today's
cloud, it's a projection of where the cloud will be found 26 bars in the
FUTURE. The cloud actually surrounding TODAY's price was computed 26 bars
AGO. This module makes that explicit with two clearly-named families:

  - `senkou_span_a_raw` / `senkou_span_b_raw` — the projection formula
    itself, using only data up to and including bar i (no future data
    involved in the computation — only the CONVENTIONAL PLOTTING position
    is forward, not the math). Useful for reading "what will the cloud
    look like 26 bars from now, given what's known today" — a legitimate
    forward-looking projection from current data, not a lookahead bug.
  - `cloud_top` / `cloud_bottom` — `.shift(displacement)` of the raw
    spans, i.e. the cloud actually surrounding TODAY's price, computed
    from data as of `displacement` bars ago. This is what "is price above
    the cloud today" must be checked against.

Chikou Span (the lagging line) is just today's close plotted `displacement`
bars in the past — checking whether it "confirms" is a comparison between
today's close and the close from `displacement` bars ago
(`close > close.shift(displacement)`), fully backward-looking.
"""

import pandas as pd

DEFAULT_TENKAN_PERIOD = 9
DEFAULT_KIJUN_PERIOD = 26
DEFAULT_SENKOU_B_PERIOD = 52
DEFAULT_DISPLACEMENT = 26


def _donchian_mid(df: pd.DataFrame, period: int) -> pd.Series:
    return (df["high"].rolling(period).max() + df["low"].rolling(period).min()) / 2


def tenkan_sen(df: pd.DataFrame, period: int = DEFAULT_TENKAN_PERIOD) -> pd.Series:
    return _donchian_mid(df, period)


def kijun_sen(df: pd.DataFrame, period: int = DEFAULT_KIJUN_PERIOD) -> pd.Series:
    return _donchian_mid(df, period)


def senkou_span_a_raw(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                       kijun_period: int = DEFAULT_KIJUN_PERIOD) -> pd.Series:
    return (tenkan_sen(df, tenkan_period) + kijun_sen(df, kijun_period)) / 2


def senkou_span_b_raw(df: pd.DataFrame, period: int = DEFAULT_SENKOU_B_PERIOD) -> pd.Series:
    return _donchian_mid(df, period)


def cloud_top(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
              kijun_period: int = DEFAULT_KIJUN_PERIOD, senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD,
              displacement: int = DEFAULT_DISPLACEMENT) -> pd.Series:
    a = senkou_span_a_raw(df, tenkan_period, kijun_period).shift(displacement)
    b = senkou_span_b_raw(df, senkou_b_period).shift(displacement)
    return pd.concat([a, b], axis=1).max(axis=1)


def cloud_bottom(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                  kijun_period: int = DEFAULT_KIJUN_PERIOD, senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD,
                  displacement: int = DEFAULT_DISPLACEMENT) -> pd.Series:
    a = senkou_span_a_raw(df, tenkan_period, kijun_period).shift(displacement)
    b = senkou_span_b_raw(df, senkou_b_period).shift(displacement)
    return pd.concat([a, b], axis=1).min(axis=1)


def price_above_cloud(df: pd.DataFrame, **kwargs) -> pd.Series:
    return df["close"] > cloud_top(df, **kwargs)


def price_below_cloud(df: pd.DataFrame, **kwargs) -> pd.Series:
    return df["close"] < cloud_bottom(df, **kwargs)


def future_cloud_bullish(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                          kijun_period: int = DEFAULT_KIJUN_PERIOD,
                          senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD) -> pd.Series:
    """The projected cloud (not yet shifted) is bullish, i.e. span A is
    forming above span B — a legitimate forward projection from today's
    data, not a lookahead bug (see module docstring)."""
    a = senkou_span_a_raw(df, tenkan_period, kijun_period)
    b = senkou_span_b_raw(df, senkou_b_period)
    return a > b


def future_cloud_bearish(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                          kijun_period: int = DEFAULT_KIJUN_PERIOD,
                          senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD) -> pd.Series:
    a = senkou_span_a_raw(df, tenkan_period, kijun_period)
    b = senkou_span_b_raw(df, senkou_b_period)
    return a < b


def tk_cross_up(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                 kijun_period: int = DEFAULT_KIJUN_PERIOD) -> pd.Series:
    tenkan = tenkan_sen(df, tenkan_period)
    kijun = kijun_sen(df, kijun_period)
    bull = tenkan > kijun
    # .astype(bool) before the bitwise ~ is required, not cosmetic: a
    # shifted boolean Series introduces NaN in the first slot, which
    # upcasts the dtype to object; ~ on an object-dtype Series of plain
    # Python bools does INTEGER bitwise inversion (~True == -2, ~False ==
    # -1), not logical negation — a real bug found via testing here (see
    # tests/test_ichimoku.py), not a style nit. market_structure.py
    # already uses this same .astype(bool) guard for the same reason.
    was_bull = bull.shift(1).fillna(False).astype(bool)
    return bull & ~was_bull


def tk_cross_down(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                   kijun_period: int = DEFAULT_KIJUN_PERIOD) -> pd.Series:
    tenkan = tenkan_sen(df, tenkan_period)
    kijun = kijun_sen(df, kijun_period)
    bear = tenkan < kijun
    was_bear = bear.shift(1).fillna(False).astype(bool)
    return bear & ~was_bear


def chikou_confirms_bullish(df: pd.DataFrame, displacement: int = DEFAULT_DISPLACEMENT) -> pd.Series:
    return df["close"] > df["close"].shift(displacement)


def chikou_confirms_bearish(df: pd.DataFrame, displacement: int = DEFAULT_DISPLACEMENT) -> pd.Series:
    return df["close"] < df["close"].shift(displacement)


def compute_ichimoku(df: pd.DataFrame, tenkan_period: int = DEFAULT_TENKAN_PERIOD,
                      kijun_period: int = DEFAULT_KIJUN_PERIOD,
                      senkou_b_period: int = DEFAULT_SENKOU_B_PERIOD,
                      displacement: int = DEFAULT_DISPLACEMENT) -> pd.DataFrame:
    d = df.copy()
    kwargs = dict(tenkan_period=tenkan_period, kijun_period=kijun_period,
                  senkou_b_period=senkou_b_period)
    d["ichi_tenkan"] = tenkan_sen(d, tenkan_period)
    d["ichi_kijun"] = kijun_sen(d, kijun_period)
    d["ichi_cloud_top"] = cloud_top(d, displacement=displacement, **kwargs)
    d["ichi_cloud_bottom"] = cloud_bottom(d, displacement=displacement, **kwargs)
    d["ichi_price_above_cloud"] = price_above_cloud(d, displacement=displacement, **kwargs)
    d["ichi_price_below_cloud"] = price_below_cloud(d, displacement=displacement, **kwargs)
    d["ichi_future_cloud_bullish"] = future_cloud_bullish(d, **kwargs)
    d["ichi_future_cloud_bearish"] = future_cloud_bearish(d, **kwargs)
    d["ichi_tk_cross_up"] = tk_cross_up(d, tenkan_period, kijun_period)
    d["ichi_tk_cross_down"] = tk_cross_down(d, tenkan_period, kijun_period)
    d["ichi_chikou_bullish"] = chikou_confirms_bullish(d, displacement)
    d["ichi_chikou_bearish"] = chikou_confirms_bearish(d, displacement)
    return d
