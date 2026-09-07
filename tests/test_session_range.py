"""
Tests for cryptobot/engines/session_range.py — the NY-timezone-anchored
opening-range engine. Uses a synthetic 5-minute UTC series spanning two
full NY calendar days so the exact boundary behavior (NaN during the
forming window, valid from window-close through day-end, NaN again at
the next day's own forming window) can be checked precisely. Dates are
chosen in July (EDT, NY = UTC-4) to avoid DST-transition ambiguity.
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.session_range import compute_session_range


def make_5m_df(start_utc: str, n_bars: int, seed: int = 501) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start_utc, periods=n_bars, freq="5min", tz="UTC")
    base = 100 + np.cumsum(rng.normal(0, 0.2, n_bars))
    rows = []
    for b in base:
        o = b + rng.normal(0, 0.05)
        c = b + rng.normal(0, 0.05)
        h = max(o, c) + abs(rng.normal(0, 0.1))
        l = min(o, c) - abs(rng.normal(0, 0.1))
        rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 10.0})
    df = pd.DataFrame(rows)
    df["dt"] = ts
    df["ts"] = (ts.astype("int64") // 10**6)
    return df[["ts", "dt", "open", "high", "low", "close", "volume"]]


class TestSessionRange:
    def test_range_is_nan_during_the_forming_window(self):
        # 2026-07-01 00:00 NY (EDT) = 2026-07-01 04:00 UTC. The window
        # [00:00, 04:00) NY spans UTC 04:00-08:00.
        df = make_5m_df("2026-07-01 04:00:00", n_bars=200)  # covers well past 08:00 UTC
        range_high, range_low = compute_session_range(df)
        # bars within [04:00, 08:00) UTC (the forming window) must be NaN
        in_window = df["dt"] < pd.Timestamp("2026-07-01 08:00:00", tz="UTC")
        assert range_high[in_window].isna().all()
        assert range_low[in_window].isna().all()

    def test_range_equals_the_windows_actual_high_low_once_closed(self):
        df = make_5m_df("2026-07-01 04:00:00", n_bars=200)
        range_high, range_low = compute_session_range(df)
        in_window = df["dt"] < pd.Timestamp("2026-07-01 08:00:00", tz="UTC")
        expected_high = df.loc[in_window, "high"].max()
        expected_low = df.loc[in_window, "low"].min()
        after_window = ~in_window
        assert np.allclose(range_high[after_window].dropna(), expected_high)
        assert np.allclose(range_low[after_window].dropna(), expected_low)

    def test_range_resets_at_the_next_ny_day_boundary(self):
        # Run for 2 full NY days: day1 window UTC 04:00-08:00 on 07-01,
        # day2 window UTC 04:00-08:00 on 07-02. NY midnight = UTC 04:00.
        df = make_5m_df("2026-07-01 04:00:00", n_bars=576)  # 2 days of 5m bars
        range_high, range_low = compute_session_range(df)

        day2_window = ((df["dt"] >= pd.Timestamp("2026-07-02 04:00:00", tz="UTC")) &
                        (df["dt"] < pd.Timestamp("2026-07-02 08:00:00", tz="UTC")))
        assert range_high[day2_window].isna().all()

        day1_high = df.loc[(df["dt"] >= pd.Timestamp("2026-07-01 04:00:00", tz="UTC")) &
                            (df["dt"] < pd.Timestamp("2026-07-01 08:00:00", tz="UTC")), "high"].max()
        day2_high = df.loc[day2_window, "high"].max()
        assert day1_high != pytest.approx(day2_high)  # sanity: genuinely different windows

        day2_after_window = df["dt"] >= pd.Timestamp("2026-07-02 08:00:00", tz="UTC")
        assert np.allclose(range_high[day2_after_window].dropna(), day2_high)


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [100, 300])
    def test_truncation_invariance(self, truncate_at):
        full = make_5m_df("2026-07-01 04:00:00", n_bars=400)
        truncated = full.iloc[:truncate_at].reset_index(drop=True)

        full_high, full_low = compute_session_range(full)
        trunc_high, trunc_low = compute_session_range(truncated)

        pd.testing.assert_series_equal(
            full_high.iloc[:truncate_at].reset_index(drop=True),
            trunc_high.reset_index(drop=True), check_names=False, obj="range_high",
        )
        pd.testing.assert_series_equal(
            full_low.iloc[:truncate_at].reset_index(drop=True),
            trunc_low.reset_index(drop=True), check_names=False, obj="range_low",
        )
