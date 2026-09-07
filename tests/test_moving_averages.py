import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import moving_averages as ma


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestSMA:
    def test_matches_hand_calculation(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = ma.sma(s, 3)
        assert result.iloc[2] == pytest.approx(2.0)  # mean(1,2,3)
        assert result.iloc[4] == pytest.approx(4.0)  # mean(3,4,5)
        assert pd.isna(result.iloc[1])


class TestALMA:
    def test_weights_sum_to_one_so_constant_series_is_unchanged(self):
        s = pd.Series([50.0] * 20)
        result = ma.alma(s, window=9)
        assert result.iloc[-1] == pytest.approx(50.0)

    def test_more_responsive_than_sma_to_a_recent_jump(self):
        # Flat then a step change — ALMA (offset=0.85, weighted toward
        # recent bars) should react more than a plain SMA of the same window.
        s = pd.Series([50.0] * 15 + [70.0] * 5)
        alma_val = ma.alma(s, window=9).iloc[-1]
        sma_val = ma.sma(s, 9).iloc[-1]
        assert alma_val > sma_val

    def test_default_matches_tradingview_convention(self):
        assert ma.DEFAULT_ALMA_WINDOW == 9
        assert ma.DEFAULT_ALMA_OFFSET == pytest.approx(0.85)
        assert ma.DEFAULT_ALMA_SIGMA == pytest.approx(6.0)


class TestEnvelope:
    def test_upper_and_lower_bracket_the_basis_by_percent(self):
        s = pd.Series(np.linspace(100, 140, 50))
        basis, upper, lower = ma.envelope(s, length=10, percent=3.0, basis="sma")
        pd.testing.assert_series_equal(upper, basis * 1.03, check_names=False)
        pd.testing.assert_series_equal(lower, basis * 0.97, check_names=False)

    def test_exponential_basis_matches_ema(self):
        s = pd.Series(np.linspace(100, 140, 50))
        basis, _, _ = ma.envelope(s, length=10, basis="ema")
        pd.testing.assert_series_equal(basis, ma.ema(s, 10), check_names=False)


class TestNoLookahead:
    def _synthetic_series(self, n: int = 120) -> pd.DataFrame:
        rng = np.random.default_rng(131)
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

        full_result = ma.compute_moving_averages(full)
        truncated_result = ma.compute_moving_averages(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("ma_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
