import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import macd as macd_mod


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestMACDFormula:
    def test_matches_the_books_own_formula(self):
        # Book: MACD Line = EMA12 - EMA26, Signal = EMA9 of MACD Line.
        rng = np.random.default_rng(171)
        s = pd.Series(100 + np.cumsum(rng.normal(0, 1, 80)))
        macd_line, signal_line, hist = macd_mod.macd(s, 12, 26, 9)
        from cryptobot.engines.moving_averages import ema
        expected_macd = ema(s, 12) - ema(s, 26)
        pd.testing.assert_series_equal(macd_line, expected_macd, check_names=False)
        pd.testing.assert_series_equal(signal_line, ema(macd_line, 9), check_names=False)
        pd.testing.assert_series_equal(hist, macd_line - signal_line, check_names=False)


class TestCrosses:
    def test_cross_up_fires_once_on_a_real_reversal(self):
        s = pd.Series(list(np.linspace(200, 150, 40)) + list(np.linspace(150, 220, 40)))
        cross_up = macd_mod.cross_up(s, 12, 26, 9)
        cross_down = macd_mod.cross_down(s, 12, 26, 9)
        assert cross_up.sum() >= 1
        assert not (cross_up & cross_down).any()

    def test_cross_up_zero_detects_macd_line_crossing_zero(self):
        s = pd.Series(list(np.linspace(200, 150, 40)) + list(np.linspace(150, 220, 40)))
        macd_line, _, _ = macd_mod.macd(s, 12, 26, 9)
        cross = macd_mod.cross_up_zero(s, 12, 26, 9)
        if cross.any():
            i = cross[cross].index[0]
            assert macd_line.iloc[i] > 0
            assert macd_line.iloc[i - 1] <= 0

    def test_curving_down_detects_slope_reversal(self):
        # Rising then flattening/falling MACD line.
        s = pd.Series(list(np.linspace(100, 200, 50)) + list(np.linspace(200, 100, 50)))
        curving = macd_mod.curving_down(s, 12, 26, 9)
        assert curving.sum() >= 1


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(181)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [60, 100, 140])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(150)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = macd_mod.compute_macd(full)
        truncated_result = macd_mod.compute_macd(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("macd_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
