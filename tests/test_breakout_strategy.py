import numpy as np
import pandas as pd
import pytest

from cryptobot.strategies import breakout as bo


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(df["ts"], unit="h", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def zigzag_from_anchors(anchors: list[float], seg_len: int = 5) -> list[float]:
    values = [float(anchors[0])]
    for i in range(1, len(anchors)):
        seg = np.linspace(anchors[i - 1], anchors[i], seg_len + 1)[1:]
        values.extend(seg.tolist())
    return values


STRUCTURE_KWARGS = dict(structure_left=3, structure_right=3, consolidation_lookback=20,
                         consolidation_percentile=0.4, breakout_lookback=15,
                         volume_lookback=15, volume_threshold=1.2, atr_len=5)


def bullish_fixture(quiet_len: int = 20, breakout_close: float = 118.0,
                     breakout_volume: float = 300.0, breakout_body_ok: bool = True) -> pd.DataFrame:
    """
    A zigzag [100, 110, 95] establishes a confirmed swing high
    (resistance=110, confirmed at idx8), then a long QUIET flat stretch
    (small, constant range -> low, stable ATR, and low volume baseline),
    then one breakout candle with a big body and volume spike.
    """
    values = zigzag_from_anchors([100, 110, 95], seg_len=5)
    rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
    for _ in range(quiet_len):
        rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 50.0})
    if breakout_body_ok:
        rows.append({"open": 100, "high": breakout_close + 1, "low": 99,
                      "close": breakout_close, "volume": breakout_volume})
    else:
        # thin poke through the level, tiny body relative to range
        rows.append({"open": 111, "high": breakout_close + 5, "low": 105,
                      "close": breakout_close, "volume": breakout_volume})
    return make_df(rows)


class TestConsolidationDetection:
    def test_flat_quiet_market_is_consolidating(self):
        rows = [{"open": 100, "high": 100.5, "low": 99.5, "close": 100, "volume": 10} for _ in range(30)]
        df = make_df(rows)
        result = bo.is_consolidating(df, atr_len=5, lookback=20, percentile=0.4)
        assert result.iloc[-1]

    def test_expanding_volatility_is_not_consolidating(self):
        rows = [{"open": 100, "high": 100.5, "low": 99.5, "close": 100, "volume": 10} for _ in range(20)]
        # sharply expanding range at the end
        for i in range(10):
            rows.append({"open": 100, "high": 100 + i * 3, "low": 100 - i * 3, "close": 100, "volume": 10})
        df = make_df(rows)
        result = bo.is_consolidating(df, atr_len=5, lookback=20, percentile=0.4)
        assert not result.iloc[-1]


class TestBreakoutSignal:
    def test_full_sequence_fires_on_the_breakout_bar(self):
        df = bullish_fixture()
        result = bo.compute_breakout(df, **STRUCTURE_KWARGS)
        assert result["long_signal"].iloc[-1]
        assert not result["short_signal"].iloc[-1]

    def test_no_signal_without_prior_consolidation(self):
        # Same breakout, but the "quiet" stretch has a STEADILY WIDENING
        # range (not just a moving level with constant width, which
        # wouldn't actually elevate ATR) — the bar right before the
        # breakout sits at the top of its own trailing ATR range, i.e.
        # genuinely NOT a contraction.
        values = zigzag_from_anchors([100, 110, 95], seg_len=5)
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
        for i in range(20):
            half_width = 1 + i * 0.6  # range widens from 2 up to ~24.4
            rows.append({"open": 100, "high": 100 + half_width, "low": 100 - half_width,
                         "close": 100, "volume": 50.0})
        rows.append({"open": 100, "high": 145, "low": 99, "close": 140, "volume": 300.0})
        df = make_df(rows)
        result = bo.compute_breakout(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]

    def test_no_signal_without_volume_confirmation(self):
        df = bullish_fixture(breakout_volume=52.0)  # barely above the quiet baseline
        result = bo.compute_breakout(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]

    def test_no_signal_on_weak_thin_candle(self):
        df = bullish_fixture(breakout_body_ok=False)
        result = bo.compute_breakout(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]

    def test_no_signal_without_a_real_level_break(self):
        # Quiet market, volume spike, strong candle — but price never
        # actually clears the established resistance (110).
        values = zigzag_from_anchors([100, 110, 95], seg_len=5)
        rows = [{"open": v, "high": v, "low": v, "close": v, "volume": 50.0} for v in values]
        for _ in range(20):
            rows.append({"open": 100, "high": 101, "low": 99, "close": 100, "volume": 50.0})
        rows.append({"open": 100, "high": 106, "low": 99, "close": 105, "volume": 300.0})  # stays under 110
        df = make_df(rows)
        result = bo.compute_breakout(df, **STRUCTURE_KWARGS)
        assert not result["long_signal"].iloc[-1]


class TestNoLookahead:
    def _synthetic_series(self, n: int = 150) -> pd.DataFrame:
        rng = np.random.default_rng(41)
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

        full_result = bo.compute_breakout(full, **STRUCTURE_KWARGS)
        truncated_result = bo.compute_breakout(truncated, **STRUCTURE_KWARGS)

        compare_cols = [c for c in full_result.columns if c.startswith("bo_") or c.endswith("_signal")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                truncated_result[col].reset_index(drop=True),
                check_names=False,
                obj=col,
            )
