import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import mfi_reversal as mr
from cryptobot.engines import money_flow_index as mfi


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def _synthetic_series(n: int = 150, seed: int = 111) -> pd.DataFrame:
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


class TestSignalComposition:
    def test_long_signal_matches_engine_cross_up(self):
        df = _synthetic_series()
        d = mr.compute_mfi_reversal(df)
        expected = mfi.cross_up_from_oversold(df, mr.DEFAULT_PERIOD, mr.DEFAULT_OVERSOLD)
        pd.testing.assert_series_equal(d["long_signal"], expected, check_names=False)

    def test_short_signal_matches_engine_cross_down(self):
        df = _synthetic_series()
        d = mr.compute_mfi_reversal(df)
        expected = mfi.cross_down_from_overbought(df, mr.DEFAULT_PERIOD, mr.DEFAULT_OVERBOUGHT)
        pd.testing.assert_series_equal(d["short_signal"], expected, check_names=False)

    def test_long_and_short_never_fire_together(self):
        df = _synthetic_series()
        d = mr.compute_mfi_reversal(df)
        assert not (d["long_signal"] & d["short_signal"]).any()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [60, 100, 140])
    def test_truncation_invariance(self, truncate_at):
        full = _synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = mr.compute_mfi_reversal(full)
        truncated_result = mr.compute_mfi_reversal(truncated)

        for col in ["long_signal", "short_signal"]:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
