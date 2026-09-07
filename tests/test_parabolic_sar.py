import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import parabolic_sar as psar_mod


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestParabolicSAR:
    def test_sustained_uptrend_keeps_dots_below_price(self):
        rows = [{"open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i, "volume": 10}
                for i in range(40)]
        df = make_df(rows)
        sar, trend = psar_mod.parabolic_sar(df)
        # Once the trend settles into "up", SAR must stay a structural
        # invariant: below the low of the corresponding bar.
        assert (trend.iloc[10:] == 1).all()
        assert (sar.iloc[10:] < df["low"].iloc[10:]).all()

    def test_sustained_downtrend_keeps_dots_above_price(self):
        rows = [{"open": 200 - i, "high": 202 - i, "low": 199 - i, "close": 199 - i, "volume": 10}
                for i in range(40)]
        df = make_df(rows)
        sar, trend = psar_mod.parabolic_sar(df)
        assert (trend.iloc[10:] == -1).all()
        assert (sar.iloc[10:] > df["high"].iloc[10:]).all()

    def test_reversal_flips_trend(self):
        rows = [{"open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i, "volume": 10}
                for i in range(30)]
        rows += [{"open": 130 - i, "high": 131 - i, "low": 128 - i, "close": 129 - i, "volume": 10}
                 for i in range(30)]
        df = make_df(rows)
        _, trend = psar_mod.parabolic_sar(df)
        assert trend.iloc[15] == 1
        assert trend.iloc[-1] == -1

    def test_dots_below_and_above_are_mutually_exclusive(self):
        rng = np.random.default_rng(191)
        rows = []
        base = 100
        for _ in range(60):
            base += rng.normal(0, 2)
            o = base
            c = base + rng.normal(0, 1)
            h = max(o, c) + abs(rng.normal(0, 1))
            l = min(o, c) - abs(rng.normal(0, 1))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10})
        df = make_df(rows)
        below = psar_mod.dots_below_price(df)
        above = psar_mod.dots_above_price(df)
        assert not (below & above).any()
        assert (below | above).all()


class TestNoLookahead:
    def _synthetic_series(self, n: int = 120) -> pd.DataFrame:
        rng = np.random.default_rng(201)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [40, 70, 100])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(120)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = psar_mod.compute_parabolic_sar(full)
        truncated_result = psar_mod.compute_parabolic_sar(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("psar")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
