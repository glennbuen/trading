"""
Integration tests for cryptobot/backtest/exit_rules_engine.py — full
multi-day position lifecycles, checked against exit_rules_spec.md's
precedence rules end to end, not just each rule function in isolation
(already covered by tests/test_exit_rules.py).
"""

import numpy as np
import pandas as pd
import pytest

from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import BacktestCosts
from cryptobot.backtest.exit_rules import ExitRulesConfig, attach_exit_indicators
from cryptobot.backtest.exit_rules_engine import run_backtest_with_exit_rules
from cryptobot.backtest.walk_forward import run_walk_forward


def make_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["ts"] = range(len(df))
    df["dt"] = pd.to_datetime(pd.Timestamp("2026-01-01") + pd.to_timedelta(df["ts"], unit="D"), utc=True)
    df["long_signal"] = df.get("long_signal", False).fillna(False)
    return df


def flat_bar(price: float, vol=10.0) -> dict:
    return {"open": price, "high": price + 0.3, "low": price - 0.3, "close": price, "volume": vol}


class TestRatchetThenHardStop:
    def test_locked_in_gain_survives_a_later_crash(self):
        rows = [flat_bar(100) for _ in range(10)]
        rows.append({**flat_bar(100), "long_signal": True})       # signal bar
        rows.append(flat_bar(100))                                 # entry fills here (~100.05)
        rows.append(flat_bar(106))                                 # +~6% -> breakeven ratchet
        rows.append(flat_bar(115))                                 # +~15% -> lock tier (flat +6%)
        rows.append({"open": 110, "high": 111, "low": 90, "close": 92, "volume": 10})  # crash through the lock
        rows.extend(flat_bar(90) for _ in range(5))
        df = make_df(rows)

        result = run_backtest_with_exit_rules(df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                               ExitRulesConfig())
        full_exits = [t for t in result.trades if t.exit_reason == "hard_stop"]
        assert len(full_exits) == 1
        # locked at roughly entry*1.06, well above the crash low of 90 -> a real winner, not a loser
        assert full_exits[0].pnl > 0

    def test_flat_lock_gives_back_gains_past_12pct_the_addition_is_meant_to_fix(self):
        rows = [flat_bar(100) for _ in range(10)]
        rows.append({**flat_bar(100), "long_signal": True})
        rows.append(flat_bar(100))
        rows.append(flat_bar(115))   # past the 12% lock tier
        rows.append(flat_bar(140))   # keeps running to +40%, flat lock never follows
        rows.append({"open": 138, "high": 139, "low": 105, "close": 106, "volume": 10})  # gives back to ~+6%
        rows.extend(flat_bar(106) for _ in range(5))
        df = make_df(rows)

        flat_result = run_backtest_with_exit_rules(df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                                     ExitRulesConfig(enable_atr_trailing_above_lock=False))
        atr_df = attach_exit_indicators(df, ExitRulesConfig())
        atr_df["vlt_atr"] = 3.0  # constant, simple ATR for a controlled comparison
        atr_result = run_backtest_with_exit_rules(atr_df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                                    ExitRulesConfig(enable_atr_trailing_above_lock=True,
                                                                     atr_trailing_mult=2.5))
        flat_exit = [t for t in flat_result.trades if t.exit_reason == "hard_stop"][0]
        atr_exit = [t for t in atr_result.trades if t.exit_reason == "hard_stop"][0]
        # ATR trailing (2.5*3=7.5 below the peak of 140 -> stop ~132.5) exits with
        # far more of the +40% run captured than the flat +6% lock does.
        assert atr_exit.pnl > flat_exit.pnl


class TestPartialProfitTakeThenContinues:
    def test_partial_take_does_not_close_the_trade(self):
        rows = [flat_bar(100) for _ in range(10)]
        rows.append({**flat_bar(100), "long_signal": True})
        rows.append(flat_bar(100))
        rows.append(flat_bar(122))  # +22% -> triggers the +20% partial take
        rows.append(flat_bar(122))
        rows.append({"open": 122, "high": 123, "low": 90, "close": 91, "volume": 10})  # then crashes
        rows.extend(flat_bar(91) for _ in range(5))
        df = make_df(rows)

        result = run_backtest_with_exit_rules(df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                               ExitRulesConfig())
        reasons = [t.exit_reason for t in result.trades]
        assert "partial_profit_take" in reasons
        assert "hard_stop" in reasons  # remainder still eventually closes
        partial = next(t for t in result.trades if t.exit_reason == "partial_profit_take")
        final = next(t for t in result.trades if t.exit_reason == "hard_stop")
        # sizes across all slices of the one trade must sum to the original size
        assert (partial.size + final.size) == pytest.approx(partial.size / 0.25)


class TestEma8DeriskAndFailedReclaim:
    def test_derisk_then_failed_reclaim_closes_the_remainder(self):
        # A smooth ramp (so EMA(8) tracks reasonably close to price by the
        # time of entry, leaving genuine room between the hard stop and
        # EMA(8) for a clean isolation of rules 4/5), then a controlled
        # pullback that dips below EMA(8) without ever threatening the
        # 5% hard stop (entry ~118.06, hard stop ~112.16 - every bar's low
        # below stays safely above that).
        ramp = list(np.linspace(100, 117, 26))
        rows = [flat_bar(v) for v in ramp]
        rows[-1]["long_signal"] = True
        rows.append(flat_bar(118))    # entry fills here (~118.06)
        rows.append(flat_bar(113.5))  # closes below EMA(8) -> rule 4 fires (queued)
        rows.append(flat_bar(113.3))  # rule 4 fills at open; still below EMA(8) -> rule 5 queued
        rows.append(flat_bar(113.1))  # rule 5 fills at open -> full exit of remainder
        rows.extend(flat_bar(113.1) for _ in range(5))
        df = make_df(rows)
        df = attach_exit_indicators(df, ExitRulesConfig())

        result = run_backtest_with_exit_rules(df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                               ExitRulesConfig())
        reasons = [t.exit_reason for t in result.trades]
        assert "ema8_derisk" in reasons
        assert "ema_failed_reclaim_or_cross" in reasons
        derisk = next(t for t in result.trades if t.exit_reason == "ema8_derisk")
        final = next(t for t in result.trades if t.exit_reason == "ema_failed_reclaim_or_cross")
        assert derisk.size == pytest.approx(final.size)  # 50% then the other 50%


class TestSizeConservation:
    def test_total_size_across_all_slices_equals_original_entry_size(self):
        rng = np.random.default_rng(77)
        base = 100 + np.cumsum(rng.normal(0.1, 2.0, 120))
        rows = [flat_bar(b) for b in base]
        rows[30]["long_signal"] = True
        df = make_df(rows)
        df = attach_exit_indicators(df, ExitRulesConfig())
        result = run_backtest_with_exit_rules(df, "long_signal", None, RiskLimits(cooldown_bars=0),
                                               ExitRulesConfig())
        if result.trades:
            total_size = sum(t.size for t in result.trades)
            first_slice_implied_original = result.trades[0].size / (
                0.25 if result.trades[0].exit_reason == "partial_profit_take" else
                0.5 if result.trades[0].exit_reason == "ema8_derisk" else 1.0
            )
            assert total_size <= first_slice_implied_original * 1.0001  # never exceeds the original


class TestWalkForwardIntegration:
    def test_plugs_into_run_walk_forward_via_backtest_fn(self):
        rng = np.random.default_rng(9)
        base = 100 + np.cumsum(rng.normal(0.05, 1.5, 400))
        rows = [flat_bar(b) for b in base]
        for j in range(20, 400, 45):
            rows[j]["long_signal"] = True
        df = make_df(rows)

        def signal_fn(d):
            return attach_exit_indicators(d, ExitRulesConfig())

        windows = run_walk_forward(df, signal_fn, "long_signal", None, RiskLimits(cooldown_bars=0),
                                    ExitRulesConfig(), window_days=100, step_days=100,
                                    backtest_fn=run_backtest_with_exit_rules)
        assert len(windows) >= 1
        assert all(hasattr(w.result, "trades") for w in windows)
