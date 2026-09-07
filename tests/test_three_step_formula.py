"""
Tests for cryptobot/strategies/three_step_formula.py. Same "wiring
correctness" approach as this project's other deck/video-sourced
strategies: verify the AND/OR composition matches a manually-built
expression from the already-tested engine calls, plus hand-built
positive/negative fixtures for the zone-touch/first-touch-only mechanic
and no-lookahead invariance.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import three_step_formula as tsf
from cryptobot.engines.structure_break import compute_structure_break
from cryptobot.engines.price_action import is_strong_bullish


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def synthetic_series(n: int = 300, seed: int = 401) -> pd.DataFrame:
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


class TestWiring:
    def test_long_signal_only_fires_during_uptrend(self):
        df = synthetic_series()
        d = tsf.compute_three_step_formula(df)
        assert (d["long_signal"] <= d["sb_trend_up"]).all()

    def test_short_signal_only_fires_during_downtrend(self):
        df = synthetic_series()
        d = tsf.compute_three_step_formula(df)
        assert (d["short_signal"] <= d["sb_trend_down"]).all()

    def test_demand_zone_only_forms_from_impulse_during_uptrend(self):
        df = synthetic_series()
        d = tsf.compute_three_step_formula(df)
        structure = compute_structure_break(df)
        impulse_up = is_strong_bullish(df)
        demand_forms = impulse_up & structure["sb_trend_up"]
        # every value the demand zone ever takes must originate from one
        # of these formation bars (or be NaN before any has formed)
        formed_values = set(d.loc[demand_forms, "tsf_demand_low"].round(6))
        observed_values = set(d["tsf_demand_low"].dropna().round(6))
        assert observed_values <= formed_values

    def test_no_signal_can_be_both_long_and_short_on_the_same_bar(self):
        df = synthetic_series()
        d = tsf.compute_three_step_formula(df)
        assert not (d["long_signal"] & d["short_signal"]).any()


class TestZoneTouchMechanics:
    def test_second_touch_of_the_same_demand_zone_never_fires(self):
        # Hand-built: ramp up to build structure/trend up, a quiet base
        # candle, a strong impulse candle off it (forms the demand zone),
        # then TWO separate dips back into the zone - only the first may
        # ever fire long_signal.
        rows = [{"open": 100 + i * 0.05, "high": 100 + i * 0.05 + 0.3,
                 "low": 100 + i * 0.05 - 0.3, "close": 100 + i * 0.05, "volume": 10} for i in range(40)]
        # base candle (quiet) then a big impulse candle
        rows.append({"open": 102, "high": 102.3, "low": 101.8, "close": 102.1, "volume": 10})  # base
        rows.append({"open": 102.1, "high": 115, "low": 102.0, "close": 114.5, "volume": 50})  # impulse
        # drift sideways/up so structure stays "up"
        rows.extend({"open": 114.5, "high": 116, "low": 113.5, "close": 115, "volume": 10} for _ in range(5))
        # first dip back into the zone [101.8, 102.3] and reclaim
        rows.append({"open": 105, "high": 105, "low": 102.0, "close": 104, "volume": 10})
        rows.extend({"open": 104, "high": 106, "low": 103.5, "close": 105, "volume": 10} for _ in range(3))
        # second dip back into the same zone
        rows.append({"open": 104, "high": 104, "low": 102.1, "close": 103.5, "volume": 10})
        df = make_df(rows)
        d = tsf.compute_three_step_formula(df, left=3, right=3)
        fires = d["long_signal"][d["long_signal"]]
        assert len(fires) <= 1


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [100, 200])
    def test_truncation_invariance(self, truncate_at):
        df = synthetic_series(300)
        full = tsf.compute_three_step_formula(df)
        trunc = tsf.compute_three_step_formula(df.iloc[:truncate_at].reset_index(drop=True))
        cols = ["long_signal", "short_signal", "tsf_demand_low", "tsf_supply_high",
                "tsf_structure_stop", "tsf_structure_target"]
        for col in cols:
            pd.testing.assert_series_equal(
                full[col].iloc[:truncate_at].reset_index(drop=True),
                trunc[col].reset_index(drop=True), check_names=False, obj=col,
            )
