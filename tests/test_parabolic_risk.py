import numpy as np
import pandas as pd
import pytest

from cryptobot.engines import parabolic_risk as pr


def make_daily_df(n: int, start: str = "2024-01-01", trend: float = 0.5, seed: int = 231) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(np.full(n, trend) + rng.normal(0, 0.3, n))
    rows = []
    for b in base:
        o = b
        c = b + rng.normal(0, 0.2)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10.0})
    df = pd.DataFrame(rows)
    df["ts"] = (pd.Timestamp(start) + pd.to_timedelta(np.arange(n), unit="D")).astype("int64") // 10**6
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


def make_weekly_df(n: int, start: str = "2024-01-01", trend: float = 0.5, seed: int = 241) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = 100 + np.cumsum(np.full(n, trend * 7) + rng.normal(0, 1, n))
    rows = []
    for b in base:
        o = b
        c = b + rng.normal(0, 0.5)
        h = max(o, c) + abs(rng.normal(0, 1))
        l = min(o, c) - abs(rng.normal(0, 1))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10.0})
    df = pd.DataFrame(rows)
    df["ts"] = (pd.Timestamp(start) + pd.to_timedelta(np.arange(n) * 7, unit="D")).astype("int64") // 10**6
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestWeeklyMerge:
    def test_daily_bar_only_sees_a_fully_closed_weekly_candle(self):
        daily = make_daily_df(60)
        weekly = make_weekly_df(10)
        merged = pr.merge_weekly_rsi_onto_daily(daily, weekly, rsi_length=5)
        # Any daily bar's weekly_rsi must come from a week whose
        # available_at (ts + 1 week) is <= that daily bar's own ts.
        weekly_rsi_raw = None
        from cryptobot.engines.oscillators import rsi
        weekly_rsi_raw = rsi(weekly["close"], 5)
        available_at = weekly["ts"] + 7 * 24 * 3600 * 1000
        for i in [20, 35, 50]:
            daily_ts = daily["ts"].iloc[i]
            eligible = available_at[available_at <= daily_ts]
            if len(eligible) == 0:
                assert pd.isna(merged.iloc[i])
            else:
                last_eligible_idx = eligible.index[-1]
                assert merged.iloc[i] == pytest.approx(weekly_rsi_raw.iloc[last_eligible_idx], nan_ok=True) \
                    if not pd.isna(weekly_rsi_raw.iloc[last_eligible_idx]) else pd.isna(merged.iloc[i])

    def test_truncating_daily_data_never_changes_an_earlier_merged_value(self):
        daily = make_daily_df(80)
        weekly = make_weekly_df(15)
        full = pr.merge_weekly_rsi_onto_daily(daily, weekly, rsi_length=5)
        truncated_daily = daily.iloc[:50].reset_index(drop=True)
        trunc = pr.merge_weekly_rsi_onto_daily(truncated_daily, weekly, rsi_length=5)
        pd.testing.assert_series_equal(
            full.iloc[:50].reset_index(drop=True), trunc.reset_index(drop=True),
            check_names=False,
        )


class TestPHRePHR:
    def test_phr_requires_all_three_conditions(self):
        daily_rsi = pd.Series([75, 65, 75, 75])
        weekly_rsi = pd.Series([71, 71, 80, 60])
        # bar0: daily=75>70, weekly=71>70, daily>weekly -> True
        # bar1: daily=65 not >70 -> False
        # bar2: daily=75>70, weekly=80>70, but daily<weekly -> False
        # bar3: daily=75>70, weekly=60 not>70 -> False
        result = pr.is_phr(daily_rsi, weekly_rsi, threshold=70)
        assert result.tolist() == [True, False, False, False]

    def test_ephr_requires_both_above_80(self):
        daily_rsi = pd.Series([85, 85, 75])
        weekly_rsi = pd.Series([85, 75, 85])
        result = pr.is_ephr(daily_rsi, weekly_rsi, threshold=80)
        assert result.tolist() == [True, False, False]

    def test_ephr_implies_phr_style_extremity_but_is_a_stricter_threshold(self):
        # Every ePHR bar should also be "parabolic" on RSI(30) terms.
        daily_rsi = pd.Series([85.0])
        assert pr.is_parabolic(daily_rsi, threshold=70).iloc[0]


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [40, 55, 70])
    def test_truncation_invariance(self, truncate_at):
        daily = make_daily_df(80)
        weekly = make_weekly_df(15)
        full_result = pr.compute_parabolic_risk(daily, weekly, rsi_length=10)
        truncated_daily = daily.iloc[:truncate_at].reset_index(drop=True)
        trunc_result = pr.compute_parabolic_risk(truncated_daily, weekly, rsi_length=10)

        compare_cols = [c for c in full_result.columns if c.startswith("pr_")]
        for col in compare_cols:
            pd.testing.assert_series_equal(
                full_result[col].iloc[:truncate_at].reset_index(drop=True),
                trunc_result[col].reset_index(drop=True),
                check_names=False, obj=col,
            )
