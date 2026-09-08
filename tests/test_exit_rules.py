"""
Tests for cryptobot/backtest/exit_rules.py's pure state-transition
functions — each of the 5 rules checked independently against hand-built
positions/bars, matching exit_rules_spec.md's own numbered rules and the
module's documented operational choices for its two ambiguous points.
"""

import pandas as pd
import pytest

from cryptobot.backtest.exit_rules import (
    ExitRulesConfig, initial_stop_price, profit_pct, check_hard_stop,
    update_ratchet_and_time_tighten, check_time_stop_exit, check_partial_profit_take,
    check_ema8_derisk, check_ema_failed_reclaim,
)


def bar(close, high=None, low=None, ema_fast=None, ema_slow=None, atr=None) -> pd.Series:
    high = close + 1 if high is None else high
    low = close - 1 if low is None else low
    d = {"open": close, "high": high, "low": low, "close": close, "vlt_atr": atr}
    if ema_fast is not None:
        d["exit_ema_fast"] = ema_fast
    if ema_slow is not None:
        d["exit_ema_slow"] = ema_slow
    return pd.Series(d)


def new_position(side="long", entry=100.0, stop=95.0) -> dict:
    return {
        "side": side, "entry": entry, "stop": stop, "highest_favorable_price": entry,
        "days_in_trade": 0, "time_stop_tightened": False, "partial_profit_taken": False,
        "rule4_active": False,
    }


class TestInitialStopAndProfitPct:
    def test_initial_stop_below_entry_for_long(self):
        assert initial_stop_price(100.0, "long", ExitRulesConfig()) == pytest.approx(95.0)

    def test_initial_stop_above_entry_for_short(self):
        assert initial_stop_price(100.0, "short", ExitRulesConfig()) == pytest.approx(105.0)

    def test_profit_pct_long_and_short(self):
        assert profit_pct(100.0, 110.0, "long") == pytest.approx(10.0)
        assert profit_pct(100.0, 90.0, "short") == pytest.approx(10.0)
        assert profit_pct(100.0, 90.0, "long") == pytest.approx(-10.0)


class TestRule1HardStop:
    def test_fires_when_bars_low_touches_stop_long(self):
        pos = new_position(side="long", stop=95.0)
        b = bar(close=96, low=94)
        assert check_hard_stop(pos, b) is not None
        assert check_hard_stop(pos, b).reason == "hard_stop"

    def test_does_not_fire_when_low_stays_above_stop(self):
        pos = new_position(side="long", stop=95.0)
        b = bar(close=97, low=96)
        assert check_hard_stop(pos, b) is None

    def test_fires_for_short_on_high_touching_stop(self):
        pos = new_position(side="short", entry=100.0, stop=105.0)
        b = bar(close=104, high=106)
        assert check_hard_stop(pos, b) is not None


class TestRatchetTiers:
    def test_stop_moves_to_breakeven_at_4pct(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=105), cfg)  # +5%
        assert pos["stop"] == pytest.approx(100.0)

    def test_stop_locks_at_flat_6pct_above_12pct_profit(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=113), cfg)  # +13%
        assert pos["stop"] == pytest.approx(106.0)

    def test_flat_lock_never_moves_again_past_12pct(self):
        pos = new_position(side="long", entry=100.0, stop=106.0)
        pos["highest_favorable_price"] = 100.0
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=140, high=141), cfg)  # +40%, way past 12%
        assert pos["stop"] == pytest.approx(106.0)  # unchanged - the documented gap the ADDITION addresses

    def test_atr_trailing_variant_moves_stop_up_with_new_highs(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["highest_favorable_price"] = 100.0
        cfg = ExitRulesConfig(enable_atr_trailing_above_lock=True, atr_trailing_mult=2.5)
        update_ratchet_and_time_tighten(pos, bar(close=113, high=114, atr=2.0), cfg)  # +13%, ATR=2 -> 114-5=109
        assert pos["stop"] == pytest.approx(109.0)
        update_ratchet_and_time_tighten(pos, bar(close=120, high=122, atr=2.0), cfg)  # new high -> 122-5=117
        assert pos["stop"] == pytest.approx(117.0)

    def test_atr_trailing_never_loosens_on_a_pullback(self):
        pos = new_position(side="long", entry=100.0, stop=109.0)
        pos["highest_favorable_price"] = 114.0
        cfg = ExitRulesConfig(enable_atr_trailing_above_lock=True, atr_trailing_mult=2.5)
        update_ratchet_and_time_tighten(pos, bar(close=110, high=111, atr=3.0), cfg)  # pullback, lower ATR-implied stop
        assert pos["stop"] == pytest.approx(109.0)  # unchanged, never loosens

    def test_stop_never_moves_below_breakeven_once_set(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=101), cfg)  # only +1%, below breakeven trigger
        assert pos["stop"] == pytest.approx(100.0)  # stays at breakeven, doesn't fall back to -5%

    def test_short_side_ratchet_mirrors_long(self):
        pos = new_position(side="short", entry=100.0, stop=105.0)
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=95), cfg)  # +5% for a short
        assert pos["stop"] == pytest.approx(100.0)


class TestTimeStopTighten:
    def test_tightens_to_3pct_at_day5_if_no_progress(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 5
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=101), cfg)  # only +1%, below 4% progress threshold
        assert pos["stop"] == pytest.approx(97.0)  # tightened to -3%
        assert pos["time_stop_tightened"] is True

    def test_does_not_tighten_if_already_made_progress(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 5
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=106), cfg)  # +6%, already past progress threshold
        assert pos["stop"] == pytest.approx(100.0)  # breakeven ratchet applies instead, not the 3% tighten

    def test_only_fires_once_at_exactly_day5(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 5
        cfg = ExitRulesConfig()
        update_ratchet_and_time_tighten(pos, bar(close=101), cfg)
        pos["days_in_trade"] = 6
        update_ratchet_and_time_tighten(pos, bar(close=95.5), cfg)  # a later, deeper move
        # the day-5 event flag must not re-fire and further tighten
        assert pos["time_stop_tightened"] is True


class TestRule2TimeStopExit:
    def test_fires_at_configured_day_if_no_progress(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 6
        cfg = ExitRulesConfig()
        action = check_time_stop_exit(pos, bar(close=101), cfg)
        assert action is not None and action.kind == "full" and action.reason == "time_stop"

    def test_does_not_fire_before_the_configured_day(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 5
        cfg = ExitRulesConfig()
        assert check_time_stop_exit(pos, bar(close=101), cfg) is None

    def test_does_not_fire_if_progress_was_made(self):
        pos = new_position(side="long", entry=100.0, stop=95.0)
        pos["days_in_trade"] = 6
        cfg = ExitRulesConfig()
        assert check_time_stop_exit(pos, bar(close=105), cfg) is None


class TestRule3PartialProfitTake:
    def test_fires_once_at_20pct(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        cfg = ExitRulesConfig()
        action = check_partial_profit_take(pos, bar(close=121), cfg)
        assert action is not None
        assert action.kind == "partial" and action.fraction == pytest.approx(0.25)
        assert pos["partial_profit_taken"] is True

    def test_does_not_refire_once_taken(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["partial_profit_taken"] = True
        cfg = ExitRulesConfig()
        assert check_partial_profit_take(pos, bar(close=130), cfg) is None

    def test_does_not_fire_below_threshold(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        cfg = ExitRulesConfig()
        assert check_partial_profit_take(pos, bar(close=115), cfg) is None


class TestRule4And5EmaDerisk:
    def test_rule4_fires_on_close_below_ema8_for_a_long(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        cfg = ExitRulesConfig()
        action = check_ema8_derisk(pos, bar(close=105, ema_slow=106), "exit_ema_fast", "exit_ema_slow", cfg)
        assert action is not None and action.kind == "partial" and action.fraction == pytest.approx(0.5)
        assert pos["rule4_active"] is True

    def test_rule4_does_not_refire_while_active(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["rule4_active"] = True
        cfg = ExitRulesConfig()
        assert check_ema8_derisk(pos, bar(close=105, ema_slow=106), "exit_ema_fast", "exit_ema_slow", cfg) is None

    def test_rule5_exits_on_failed_reclaim(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["rule4_active"] = True
        today = bar(close=104, ema_fast=105, ema_slow=106)  # still below ema_slow -> failed reclaim
        yesterday = bar(close=105, ema_fast=106, ema_slow=106)
        action = check_ema_failed_reclaim(pos, today, yesterday, "exit_ema_fast", "exit_ema_slow", ExitRulesConfig())
        assert action is not None and action.kind == "full"

    def test_rule5_resets_on_successful_reclaim(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["rule4_active"] = True
        today = bar(close=108, ema_fast=107, ema_slow=106)  # reclaimed above ema_slow
        yesterday = bar(close=104, ema_fast=105, ema_slow=106)
        action = check_ema_failed_reclaim(pos, today, yesterday, "exit_ema_fast", "exit_ema_slow", ExitRulesConfig())
        assert action is None
        assert pos["rule4_active"] is False

    def test_rule5_exits_on_ema_cross_even_if_reclaimed(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        pos["rule4_active"] = True
        today = bar(close=107, ema_fast=105, ema_slow=106)  # reclaimed close, but fast crossed below slow
        yesterday = bar(close=104, ema_fast=107, ema_slow=106)  # fast was above slow yesterday
        action = check_ema_failed_reclaim(pos, today, yesterday, "exit_ema_fast", "exit_ema_slow", ExitRulesConfig())
        assert action is not None and action.kind == "full"

    def test_rule5_is_a_noop_when_rule4_never_fired(self):
        pos = new_position(side="long", entry=100.0, stop=100.0)
        today = bar(close=104, ema_fast=105, ema_slow=106)
        yesterday = bar(close=105, ema_fast=106, ema_slow=106)
        assert check_ema_failed_reclaim(pos, today, yesterday, "exit_ema_fast", "exit_ema_slow", ExitRulesConfig()) is None
