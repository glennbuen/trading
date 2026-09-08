import numpy as np
import pandas as pd
import pytest

from cryptobot.engines.multi_timeframe import merge_higher_timeframe_series

EPOCH_MS = int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000)
DAY_MS = 86_400_000


def make_daily(n: int) -> pd.DataFrame:
    ts = EPOCH_MS + np.arange(n) * DAY_MS
    return pd.DataFrame({"ts": ts, "dt": pd.to_datetime(ts, unit="ms", utc=True)})


def make_weekly(n: int) -> pd.DataFrame:
    ts = EPOCH_MS + np.arange(n) * 7 * DAY_MS
    return pd.DataFrame({"ts": ts, "dt": pd.to_datetime(ts, unit="ms", utc=True)})


class TestMergeHigherTimeframeSeries:
    def test_nan_before_the_first_weekly_bar_has_closed(self):
        daily = make_daily(10)
        weekly = make_weekly(3)
        weekly_series = pd.Series([10.0, 20.0, 30.0])
        merged = merge_higher_timeframe_series(daily, weekly, weekly_series, "1w")
        # week 0 spans days 0-6, only available starting day 7
        assert merged.iloc[:7].isna().all()

    def test_value_becomes_available_exactly_when_the_week_closes(self):
        daily = make_daily(20)
        weekly = make_weekly(3)
        weekly_series = pd.Series([10.0, 20.0, 30.0])
        merged = merge_higher_timeframe_series(daily, weekly, weekly_series, "1w")
        assert merged.iloc[6] != pytest.approx(10.0) or pd.isna(merged.iloc[6])  # not yet available at day 6
        assert merged.iloc[7] == pytest.approx(10.0)  # available starting day 7 (week 0 closed)
        assert merged.iloc[13] == pytest.approx(10.0)  # still week 0's value through day 13
        assert merged.iloc[14] == pytest.approx(20.0)  # week 1 closed -> new value

    def test_works_with_boolean_series(self):
        daily = make_daily(20)
        weekly = make_weekly(3)
        weekly_bool = pd.Series([True, False, True])
        merged = merge_higher_timeframe_series(daily, weekly, weekly_bool, "1w")
        assert bool(merged.iloc[7]) is True
        assert bool(merged.iloc[14]) is False


class TestNoLookahead:
    @pytest.mark.parametrize("truncate_at", [10, 25])
    def test_truncation_invariance(self, truncate_at):
        daily = make_daily(40)
        weekly = make_weekly(6)
        weekly_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        full = merge_higher_timeframe_series(daily, weekly, weekly_series, "1w")
        trunc_daily = daily.iloc[:truncate_at].reset_index(drop=True)
        trunc = merge_higher_timeframe_series(trunc_daily, weekly, weekly_series, "1w")
        pd.testing.assert_series_equal(
            full.iloc[:truncate_at].reset_index(drop=True),
            trunc.reset_index(drop=True), check_names=False,
        )
