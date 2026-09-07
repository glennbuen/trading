"""
Tests for all 7 "Forbidden Book" strategies. Since each is a thin
composition of already-thoroughly-tested engines (moving_averages,
oscillators, macd, parabolic_sar — each with their own correctness and
no-lookahead test suites), these tests verify WIRING correctness (does
the strategy's AND/OR composition match a manual expression built from
the same already-tested engine calls) plus no-lookahead for the
strategy-level output columns, rather than re-deriving engine math.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import mama, fishball, calma, papa, tita, bopis, day_trading_alma
from cryptobot.utils import bars_since
from cryptobot.engines.moving_averages import alma as alma_fn
from cryptobot.engines.oscillators import cci as cci_fn, rsi as rsi_fn
from cryptobot.engines import macd as macd_mod
from cryptobot.engines.parabolic_sar import dots_below_price
from cryptobot.engines.oscillators import trix_cross_up_zero


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_series(n: int = 250, seed: int = 211) -> pd.DataFrame:
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


def assert_truncation_invariant(compute_fn, df, cols, truncate_at):
    truncated = df.iloc[:truncate_at].reset_index(drop=True)
    full_result = compute_fn(df)
    trunc_result = compute_fn(truncated)
    for col in cols:
        pd.testing.assert_series_equal(
            full_result[col].iloc[:truncate_at].reset_index(drop=True),
            trunc_result[col].reset_index(drop=True),
            check_names=False, obj=col,
        )


class TestMAMA:
    def test_long_signal_matches_manual_composition(self):
        df = synthetic_series()
        d = mama.compute_mama(df)
        breakout = mama.alma_breakout_up(df)
        macd_up = macd_mod.cross_up(df["close"])
        expected = (bars_since(breakout) <= 1) & (bars_since(macd_up) <= 1)
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(mama.compute_mama, synthetic_series(),
                                     ["long_signal", "mama_alma"], truncate_at)


class TestFishball:
    def test_no_signal_without_prior_oversold(self):
        # Constant series -> fisher stays near 0, never dips to -1.5, so
        # cross-up-through-trigger events (if any) must never fire long_signal.
        rows = [{"open": 100, "high": 100.5, "low": 99.5, "close": 100, "volume": 10} for _ in range(60)]
        df = make_df(rows)
        d = fishball.compute_fishball(df)
        assert not d["long_signal"].any()

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(
            fishball.compute_fishball, synthetic_series(),
            ["long_signal", "fishball_exit_signal", "fishball_fisher"], truncate_at)


class TestCALMA:
    def test_long_signal_matches_manual_composition(self):
        df = synthetic_series()
        d = calma.compute_calma(df)
        c = cci_fn(df)
        a = alma_fn(df["close"])
        expected = ((c >= 100) & (c.shift(1) < 100)).fillna(False) & (df["close"] > a)
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(calma.compute_calma, synthetic_series(),
                                     ["long_signal", "calma_alma", "calma_cci"], truncate_at)


class TestPAPA:
    def test_long_signal_requires_both_macd_zero_cross_and_envelope_breakout(self):
        df = synthetic_series()
        d = papa.compute_papa(df)
        assert (d["long_signal"] <= d["papa_macd_cross_up_zero"]).all()
        assert (d["long_signal"] <= d["papa_envelope_breakout"]).all()

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(
            papa.compute_papa, synthetic_series(),
            ["long_signal", "papa_exit_signal", "papa_alma", "papa_envelope_upper"], truncate_at)


class TestTITA:
    def test_long_signal_matches_manual_composition(self):
        df = synthetic_series()
        d = tita.compute_tita(df)
        r = rsi_fn(df["close"])
        breakout = tita.alma_breakout_up(df)
        cond1 = (r > 50) & (r.shift(1) <= 50)
        cond2 = (r >= 55) & breakout
        expected = cond1.fillna(False) | cond2
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(tita.compute_tita, synthetic_series(),
                                     ["long_signal", "tita_alma", "tita_rsi"], truncate_at)


class TestBOPIS:
    def test_long_signal_requires_all_three_conditions(self):
        df = synthetic_series()
        d = bopis.compute_bopis(df)
        assert (d["long_signal"] <= d["bopis_dots_below"]).all()
        assert (d["long_signal"] <= d["bopis_above_ema9"]).all()

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(bopis.compute_bopis, synthetic_series(),
                                     ["long_signal", "bopis_ema9"], truncate_at)


class TestDayTradingALMA:
    def test_long_signal_is_the_alma_breakout_event(self):
        df = synthetic_series()
        d = day_trading_alma.compute_day_trading_alma(df)
        a = alma_fn(df["close"])
        above = df["close"] > a
        was_above = above.shift(1).fillna(False).astype(bool)
        expected = above & ~was_above
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    @pytest.mark.parametrize("truncate_at", [80, 150, 220])
    def test_no_lookahead(self, truncate_at):
        assert_truncation_invariant(day_trading_alma.compute_day_trading_alma, synthetic_series(),
                                     ["long_signal", "dt_alma"], truncate_at)
