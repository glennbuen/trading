import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import volatility as vlt


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestTrueRange:
    def test_simple_case_matches_hand_calculation(self):
        rows = [
            {"open": 100, "high": 105, "low": 98, "close": 102, "volume": 1},
            {"open": 102, "high": 110, "low": 101, "close": 108, "volume": 1},  # gap up from prev close 102
        ]
        df = make_df(rows)
        tr = vlt.true_range(df)
        # bar 0: no prior close -> high-low = 7
        assert tr.iloc[0] == pytest.approx(7.0)
        # bar 1: max(high-low=9, |high-prevclose|=8, |low-prevclose|=1) = 9
        assert tr.iloc[1] == pytest.approx(9.0)

    def test_gap_down_uses_prev_close_distance(self):
        rows = [
            {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 1},
            {"open": 80, "high": 82, "low": 78, "close": 81, "volume": 1},  # big gap down
        ]
        df = make_df(rows)
        tr = vlt.true_range(df)
        # bar1: max(high-low=4, |82-100|=18, |78-100|=22) = 22
        assert tr.iloc[1] == pytest.approx(22.0)


class TestATR:
    def test_atr_is_smoothed_true_range(self):
        rng = np.random.default_rng(5)
        rows = []
        base = 100
        for _ in range(50):
            base += rng.normal(0, 1)
            o = base
            c = base + rng.normal(0, 0.5)
            h = max(o, c) + abs(rng.normal(0, 1))
            l = min(o, c) - abs(rng.normal(0, 1))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 1})
        df = make_df(rows)
        atr = vlt.atr(df, length=14)
        tr = vlt.true_range(df)
        # ATR should be smoother (lower variance) than raw true range.
        assert atr.iloc[20:].std() < tr.iloc[20:].std()
        assert (atr.iloc[20:] > 0).all()

    def test_atr_pct_scales_with_price(self):
        rows = [{"open": 100, "high": 102, "low": 98, "close": 100, "volume": 1} for _ in range(20)]
        df_cheap = make_df(rows)
        rows_expensive = [{"open": 10000, "high": 10200, "low": 9800, "close": 10000, "volume": 1} for _ in range(20)]
        df_expensive = make_df(rows_expensive)
        # Same relative volatility (2% range) at two different price scales
        # should give roughly the same atr_pct.
        pct_cheap = vlt.atr_pct(df_cheap, length=14).iloc[-1]
        pct_expensive = vlt.atr_pct(df_expensive, length=14).iloc[-1]
        assert pct_cheap == pytest.approx(pct_expensive, rel=0.01)


class TestNoLookahead:
    def _synthetic_series(self, n: int = 100) -> pd.DataFrame:
        rng = np.random.default_rng(17)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 1})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [30, 60, 90])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(100)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = vlt.compute_volatility(full)
        truncated_result = vlt.compute_volatility(truncated)

        for col in ["vlt_true_range", "vlt_atr", "vlt_atr_pct"]:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
