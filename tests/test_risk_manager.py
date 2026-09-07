import pandas as pd
import pytest

from cryptobot.risk.position_sizing import calculate_size
from cryptobot.risk.risk_manager import RiskLimits, RiskManager


class TestPositionSizing:
    def test_matches_the_architecture_spec_worked_example(self):
        # Account=$10,000, risk=0.5% -> max loss $50, stop distance=$100 -> size=0.5.
        # max_position_pct given plenty of headroom (300%) so this isolates
        # the risk-based formula itself from the leverage cap (tested
        # separately below) — 0.5 units @ $50,000 is $25,000 notional, a
        # real 2.5x-leveraged position the cap would otherwise correctly
        # reject at max_position_pct=100.
        size = calculate_size(equity=10_000, risk_pct=0.5, entry_price=50_000,
                               stop_price=49_900, max_position_pct=300)
        assert size == pytest.approx(0.5)

    def test_capped_by_max_position_pct(self):
        # Risk-based size would be huge (tiny stop distance) but must be
        # capped at max_position_pct of equity notional.
        size = calculate_size(equity=10_000, risk_pct=1.0, entry_price=100,
                               stop_price=99.99, max_position_pct=25)
        max_notional = 10_000 * 0.25
        assert size * 100 <= max_notional + 1e-6

    def test_zero_stop_distance_returns_zero(self):
        assert calculate_size(10_000, 1.0, 100, 100, 25) == 0.0

    def test_non_positive_equity_returns_zero(self):
        assert calculate_size(0, 1.0, 100, 90, 25) == 0.0
        assert calculate_size(-500, 1.0, 100, 90, 25) == 0.0


class TestRiskManagerLimits:
    def test_rejects_when_daily_loss_limit_hit(self):
        rm = RiskManager(RiskLimits(max_daily_loss_pct=2.0), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.mark_time(dt)
        rm.register_position_closed(pnl=-25, dt=dt, bar_index=0, notional_pct_of_equity=10)  # -2.5%
        allowed, reason = rm.can_open_position(dt, bar_index=1)
        assert not allowed
        assert reason == "daily_loss_limit"

    def test_daily_loss_resets_on_new_calendar_day(self):
        # bar_index gap kept well past cooldown_bars so this isolates the
        # daily-loss-window reset specifically, not the (separately
        # tested) cooldown-after-a-close behavior.
        rm = RiskManager(RiskLimits(max_daily_loss_pct=2.0, cooldown_bars=1), starting_equity=1000)
        day1 = pd.Timestamp("2026-01-01T12:00:00Z")
        rm.register_position_closed(pnl=-25, dt=day1, bar_index=0, notional_pct_of_equity=10)
        allowed, reason = rm.can_open_position(day1, bar_index=5)
        assert not allowed
        assert reason == "daily_loss_limit"
        day2 = pd.Timestamp("2026-01-02T00:00:00Z")
        allowed, _ = rm.can_open_position(day2, bar_index=10)
        assert allowed

    def test_weekly_loss_limit(self):
        rm = RiskManager(RiskLimits(max_daily_loss_pct=100, max_weekly_loss_pct=3.0), starting_equity=1000)
        d = pd.Timestamp("2026-01-05T00:00:00Z")  # Monday
        rm.register_position_closed(pnl=-40, dt=d, bar_index=0, notional_pct_of_equity=10)  # -4%
        allowed, reason = rm.can_open_position(d, bar_index=1)
        assert not allowed
        assert reason == "weekly_loss_limit"

    def test_consecutive_losses_trigger_halt(self):
        rm = RiskManager(RiskLimits(max_consecutive_losses=3, halt_cooldown_hours=24,
                                     max_daily_loss_pct=100), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        for i in range(3):
            rm.register_position_closed(pnl=-1, dt=dt, bar_index=i, notional_pct_of_equity=5)
        allowed, reason = rm.can_open_position(dt, bar_index=10)
        assert not allowed
        assert reason == "circuit_breaker_halt"
        # halt expires after the cooldown
        later = dt + pd.Timedelta(hours=25)
        allowed, _ = rm.can_open_position(later, bar_index=11)
        assert allowed

    def test_a_win_resets_consecutive_loss_counter(self):
        rm = RiskManager(RiskLimits(max_consecutive_losses=3, max_daily_loss_pct=100), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.register_position_closed(pnl=-1, dt=dt, bar_index=0, notional_pct_of_equity=5)
        rm.register_position_closed(pnl=-1, dt=dt, bar_index=1, notional_pct_of_equity=5)
        rm.register_position_closed(pnl=+5, dt=dt, bar_index=2, notional_pct_of_equity=5)
        assert rm.consecutive_losses == 0

    def test_max_open_positions_enforced(self):
        rm = RiskManager(RiskLimits(max_open_positions=1, max_daily_loss_pct=100), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.register_position_opened(notional_pct_of_equity=10)
        allowed, reason = rm.can_open_position(dt, bar_index=1)
        assert not allowed
        assert reason == "max_open_positions"

    def test_max_exposure_enforced(self):
        rm = RiskManager(RiskLimits(max_portfolio_exposure_pct=20, max_open_positions=10,
                                     max_daily_loss_pct=100), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.register_position_opened(notional_pct_of_equity=25)
        allowed, reason = rm.can_open_position(dt, bar_index=1)
        assert not allowed
        assert reason == "max_exposure"

    def test_cooldown_after_a_close(self):
        rm = RiskManager(RiskLimits(cooldown_bars=5, max_daily_loss_pct=100), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.register_position_closed(pnl=1, dt=dt, bar_index=10, notional_pct_of_equity=5)
        allowed, reason = rm.can_open_position(dt, bar_index=12)
        assert not allowed
        assert reason == "cooldown"
        allowed, _ = rm.can_open_position(dt, bar_index=16)
        assert allowed

    def test_emergency_shutdown_blocks_everything(self):
        rm = RiskManager(RiskLimits(), starting_equity=1000)
        dt = pd.Timestamp("2026-01-01T00:00:00Z")
        rm.trigger_emergency_shutdown("unexpected position detected")
        allowed, reason = rm.can_open_position(dt, bar_index=0)
        assert not allowed
        assert reason == "emergency_shutdown"

    def test_position_size_uses_current_equity(self):
        rm = RiskManager(RiskLimits(risk_per_trade_pct=1.0, max_position_pct=100), starting_equity=1000)
        size = rm.position_size(entry_price=100, stop_price=90)
        assert size == pytest.approx(1.0)  # $10 risk / $10 stop distance
