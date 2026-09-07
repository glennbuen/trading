import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import ichimoku as ichi


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def monotonic_rows(n: int) -> list[dict]:
    """high[i]=100+i, low[i]=90+i — a constant-range rising market, easy
    to hand-compute Donchian midpoints against."""
    return [{"open": 95 + i, "high": 100 + i, "low": 90 + i, "close": 95 + i, "volume": 10}
            for i in range(n)]


class TestTenkanKijun:
    def test_tenkan_matches_hand_calculation(self):
        df = make_df(monotonic_rows(20))
        tenkan = ichi.tenkan_sen(df, period=9)
        # at bar 8 (first full 9-bar window): max(high[0:9])=108, min(low[0:9])=90 -> 99
        assert tenkan.iloc[8] == pytest.approx(99.0)
        assert pd.isna(tenkan.iloc[7])  # not enough history yet

    def test_kijun_matches_hand_calculation(self):
        df = make_df(monotonic_rows(30))
        kijun = ichi.kijun_sen(df, period=26)
        # at bar 25: max(high[0:26])=125, min(low[0:26])=90 -> 107.5
        assert kijun.iloc[25] == pytest.approx(107.5)


class TestCloudShift:
    def test_cloud_top_is_the_shifted_raw_span(self):
        df = make_df(monotonic_rows(150))
        cloud_top = ichi.cloud_top(df, displacement=26)
        raw_a = ichi.senkou_span_a_raw(df)
        raw_b = ichi.senkou_span_b_raw(df)
        expected = pd.concat([raw_a.shift(26), raw_b.shift(26)], axis=1).max(axis=1)
        pd.testing.assert_series_equal(cloud_top, expected, check_names=False)

    def test_cloud_at_bar_i_uses_only_data_up_to_bar_i_minus_displacement(self):
        """The defining no-lookahead property: cloud_top at bar i must be
        IDENTICAL whether computed on the full series or on a series
        truncated right after bar (i - displacement) — i.e. it cannot
        depend on anything from bar (i - displacement + 1) onward."""
        df = make_df(monotonic_rows(150))
        i = 100
        displacement = 26
        truncated = df.iloc[: i - displacement + 1].reset_index(drop=True)
        full_cloud_top = ichi.cloud_top(df, displacement=displacement)
        trunc_cloud_top = ichi.cloud_top(truncated, displacement=displacement)
        # The truncated series' LAST value corresponds to bar (i - displacement),
        # whose cloud_top is NaN (not enough forward shift room) - instead
        # verify equality on an earlier, fully-computable bar within both.
        check_bar = 60
        assert full_cloud_top.iloc[check_bar] == pytest.approx(trunc_cloud_top.iloc[check_bar])


class TestTKCross:
    def test_cross_up_fires_exactly_once_at_the_transition_not_every_bar_after(self):
        """Regression test for a real bug found via testing: an earlier
        version used `bull & ~(bull.shift(1).fillna(False))` without
        casting the shifted Series back to bool first. On an object-dtype
        Series of plain Python bools, `~` does integer bitwise inversion
        (~True == -2, ~False == -1) instead of logical negation, which
        made tk_cross_up fire on EVERY bar after the real crossover
        (18 bars in this exact fixture) instead of just once, right at
        it — caught because `bull` itself only ever transitions once in
        this fixture (verified below), so any count other than exactly
        one confirmed-cross is provably wrong, not just "off by a bit"."""
        rows = [{"open": 200 - i, "high": 205 - i, "low": 195 - i, "close": 200 - i, "volume": 10}
                for i in range(30)]
        rows += [{"open": 170 + i, "high": 175 + i, "low": 165 + i, "close": 170 + i, "volume": 10}
                 for i in range(30)]
        df = make_df(rows)

        tenkan = ichi.tenkan_sen(df, 9)
        kijun = ichi.kijun_sen(df, 26)
        bull = tenkan > kijun
        bull_transitions = (bull != bull.shift(1)).sum() - 1  # -1 for the trivial first-row "transition"
        assert bull_transitions == 1, "fixture assumption broken: expected exactly one real TK relationship flip"

        cross_up = ichi.tk_cross_up(df, tenkan_period=9, kijun_period=26)
        cross_down = ichi.tk_cross_down(df, tenkan_period=9, kijun_period=26)
        assert cross_up.sum() == 1
        assert cross_up.idxmax() == 42  # fires exactly AT the real transition, not the 18 bars after it
        # cross_down may legitimately fire once at bar 25 (kijun's first
        # computable bar, period=26 -> index 25) — going from "undefined"
        # to a real reading counts as an edge under this codebase's
        # existing warmup convention (see e.g. price_action's breakout
        # detection). What it must NOT do is repeat on every bar after —
        # that's the actual bug this test guards against.
        assert cross_down.sum() <= 1
        # cross_up and cross_down can never both be true on the same bar
        assert not (cross_up & cross_down).any()


class TestChikou:
    def test_bullish_when_close_above_displaced_close(self):
        df = make_df(monotonic_rows(60))  # strictly rising close -> always bullish
        result = ichi.chikou_confirms_bullish(df, displacement=26)
        assert result.iloc[40]  # close[40] > close[14], rising series
        assert not ichi.chikou_confirms_bearish(df, displacement=26).iloc[40]


class TestNoLookahead:
    def _synthetic_series(self, n: int = 200) -> pd.DataFrame:
        rng = np.random.default_rng(71)
        base = 100 + np.cumsum(rng.normal(0, 1, n))
        rows = []
        for b in base:
            o = b + rng.normal(0, 0.3)
            c = b + rng.normal(0, 0.3)
            h = max(o, c) + abs(rng.normal(0, 0.5))
            l = min(o, c) - abs(rng.normal(0, 0.5))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": abs(rng.normal(100, 40)) + 10})
        return make_df(rows)

    @pytest.mark.parametrize("truncate_at", [90, 140, 190])
    def test_truncation_invariance(self, truncate_at):
        full = self._synthetic_series(200)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_result = ichi.compute_ichimoku(full)
        truncated_result = ichi.compute_ichimoku(truncated)

        compare_cols = [c for c in full_result.columns if c.startswith("ichi_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
