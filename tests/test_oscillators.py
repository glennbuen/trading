import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import oscillators as osc


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestRSI:
    def test_strictly_rising_series_pushes_rsi_high(self):
        s = pd.Series(np.linspace(100, 150, 30))
        result = osc.rsi(s, length=14)
        assert result.iloc[-1] > 70

    def test_strictly_falling_series_pushes_rsi_low(self):
        s = pd.Series(np.linspace(150, 100, 30))
        result = osc.rsi(s, length=14)
        assert result.iloc[-1] < 30

    def test_bounded_0_to_100(self):
        rng = np.random.default_rng(141)
        s = pd.Series(100 + np.cumsum(rng.normal(0, 2, 100)))
        result = osc.rsi(s, length=14).dropna()
        assert (result >= 0).all() and (result <= 100).all()


class TestCCI:
    def test_price_at_top_of_its_range_gives_positive_cci(self):
        # Oscillating range, then a clear push to a new high relative to
        # its own recent range -> CCI should read positive/high.
        rows = [{"open": 100, "high": 102, "low": 98, "close": 100, "volume": 10} for _ in range(20)]
        rows.append({"open": 100, "high": 115, "low": 100, "close": 114, "volume": 10})
        df = make_df(rows)
        result = osc.cci(df, length=20)
        assert result.iloc[-1] > 100


class TestFisherTransform:
    def test_price_pinned_at_top_of_range_gives_large_positive_fisher(self):
        rows = [{"open": 100, "high": 100 + i, "low": 100 - i, "close": 100, "volume": 10} for i in range(15)]
        # last bar: median price at the top of its own trailing range
        rows.append({"open": 100, "high": 120, "low": 118, "close": 119, "volume": 10})
        df = make_df(rows)
        fisher, trigger = osc.fisher_transform(df, length=9)
        assert fisher.iloc[-1] > 0

    def test_trigger_is_fisher_lagged_by_one_bar(self):
        rng = np.random.default_rng(151)
        rows = []
        base = 100
        for _ in range(40):
            base += rng.normal(0, 1)
            o = base
            c = base + rng.normal(0, 0.5)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10})
        df = make_df(rows)
        fisher, trigger = osc.fisher_transform(df, length=9)
        pd.testing.assert_series_equal(trigger, fisher.shift(1), check_names=False)


class TestTrix:
    def test_rising_series_gives_positive_trix(self):
        s = pd.Series(np.linspace(100, 200, 80))
        result = osc.trix(s, length=18)
        assert result.iloc[-1] > 0

    def test_falling_series_gives_negative_trix(self):
        s = pd.Series(np.linspace(200, 100, 80))
        result = osc.trix(s, length=18)
        assert result.iloc[-1] < 0


class TestNoLookahead:
    def _synthetic_series(self, n: int = 120) -> pd.DataFrame:
        rng = np.random.default_rng(161)
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

        full_result = osc.compute_oscillators(full)
        truncated_result = osc.compute_oscillators(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("osc_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
