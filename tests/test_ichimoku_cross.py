import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import ichimoku_cross as ic


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def _synthetic_series(n: int = 200, seed: int = 81) -> pd.DataFrame:
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
    def test_long_signal_requires_all_four_conditions(self):
        """The underlying ichimoku engine columns are already thoroughly
        tested (tests/test_ichimoku.py) — this checks only that the
        strategy layer correctly ANDs all four, by construction, against
        real computed columns rather than restating the code with mocks."""
        df = _synthetic_series()
        d = ic.compute_ichimoku_cross(df)
        manual_long = (d["ichi_tk_cross_up"] & d["ichi_price_above_cloud"] &
                       d["ichi_future_cloud_bullish"] & d["ichi_chikou_bullish"])
        pd.testing.assert_series_equal(d["long_signal"], manual_long, check_names=False)

        manual_short = (d["ichi_tk_cross_down"] & d["ichi_price_below_cloud"] &
                        d["ichi_future_cloud_bearish"] & d["ichi_chikou_bearish"])
        pd.testing.assert_series_equal(d["short_signal"], manual_short, check_names=False)

    def test_long_and_short_never_fire_on_the_same_bar(self):
        df = _synthetic_series()
        d = ic.compute_ichimoku_cross(df)
        assert not (d["long_signal"] & d["short_signal"]).any()

    def test_kijun_stop_column_matches_kijun_sen(self):
        df = _synthetic_series()
        d = ic.compute_ichimoku_cross(df)
        pd.testing.assert_series_equal(d["ichi_kijun_stop"], d["ichi_kijun"], check_names=False)

    def test_dropping_any_single_condition_would_fire_more_often(self):
        """Spec §15: no single indicator should trigger a trade alone.
        Verified structurally: each individual condition is true strictly
        more often (or equal) than the full AND of all four."""
        df = _synthetic_series()
        d = ic.compute_ichimoku_cross(df)
        for col in ["ichi_tk_cross_up", "ichi_price_above_cloud",
                    "ichi_future_cloud_bullish", "ichi_chikou_bullish"]:
            assert d[col].sum() >= d["long_signal"].sum()


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [90, 140, 190])
    def test_truncation_invariance(self, truncate_at):
        full = _synthetic_series(200)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = ic.compute_ichimoku_cross(full)
        truncated_result = ic.compute_ichimoku_cross(truncated)

        compare_cols = ["long_signal", "short_signal", "ichi_kijun_stop"]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
