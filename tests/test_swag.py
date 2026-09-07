"""
Tests for the SWAG Trading System (cryptobot/strategies/swag.py). Same
"wiring correctness" approach as test_book_strategies.py /
test_spyfrat_strategies.py — swag.py is a thin composition of already-
tested engines (parabolic_sar, moving_averages, money_flow_index), so
these tests verify the AND/OR composition matches a manually-built
expression from the same engine calls, plus no-lookahead invariance.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import swag
from cryptobot.engines.parabolic_sar import dots_below_price, dots_above_price
from cryptobot.engines.moving_averages import ema, sma
from cryptobot.engines.money_flow_index import money_flow_index, cross_down_from_overbought


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_series(n: int = 250, seed: int = 271) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(rng.normal(0, 1, n))
    rows = []
    for b in base:
        o = b + rng.normal(0, 0.3)
        c = b + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.5))
        l = min(o, c) - abs(rng.normal(0, 0.5))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
    return make_df(rows)


class TestSwag:
    def test_long_signal_matches_manual_composition(self):
        df = synthetic_series()
        d = swag.compute_swag(df)

        trend_up = dots_below_price(df)
        cross_up = swag.ema_cross_up_sma(df)
        mfi = money_flow_index(df)
        expected = trend_up.fillna(False) & cross_up.fillna(False) & (mfi > 50).fillna(False)

        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    def test_exit_signal_matches_manual_composition(self):
        df = synthetic_series()
        d = swag.compute_swag(df)

        cross_down = swag.ema_cross_down_sma(df)
        trend_up = dots_below_price(df)
        trend_down = dots_above_price(df)
        trend_flip_down = trend_up.shift(1).fillna(False).astype(bool) & trend_down.fillna(False)
        mfi_exit = cross_down_from_overbought(df)
        expected = cross_down.fillna(False) | trend_flip_down | mfi_exit.fillna(False)

        pd.testing.assert_series_equal(d["swag_exit_signal"], expected, check_names=False)

    def test_long_signal_never_fires_without_ema_cross_up(self):
        # long_signal must always imply an EMA/SMA cross-up bar occurred
        # on that same bar - it's an AND'd component, not just a filter.
        df = synthetic_series()
        d = swag.compute_swag(df)
        assert (d["long_signal"] <= d["swag_cross_up"]).all()

    def test_no_signal_when_trend_is_down(self):
        # Hand-built clean downtrend: EMA13/SMA20 cross events can still
        # occur inside noise, but the SAR trend filter must veto every
        # single one of them if trend never goes up.
        n = 80
        vals = np.linspace(200, 100, n)
        rows = [{"open": v, "high": v + 0.5, "low": v - 0.5, "close": v, "volume": 10} for v in vals]
        df = make_df(rows)
        d = swag.compute_swag(df)
        if not d["swag_trend_up"].any():
            assert not d["long_signal"].any()

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        df = synthetic_series(250)
        full = swag.compute_swag(df)
        trunc = swag.compute_swag(df.iloc[:truncate_at].reset_index(drop=True))
        for col in ["long_signal", "swag_exit_signal", "swag_ema", "swag_sma", "swag_mfi", "swag_trend_up"]:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
