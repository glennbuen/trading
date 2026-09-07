"""
RiskManager — centralizes what was previously duplicated per-bot across
this project's 7 standalone scripts: position sizing, daily/weekly loss
limits, max consecutive losses, cooldown, max open positions/exposure,
and an emergency kill switch (architecture spec §16).

Risk management has priority over trade frequency: can_open_position()
is the single gate every strategy's entry signal must pass through before
the backtest engine (or, later, the live/paper loop) is allowed to open a
trade. Nothing bypasses it.

Day/week boundaries are computed from actual UTC timestamps (calendar
date / ISO week), not bar-count heuristics (`bars_per_day = 24/tf_hours`)
like the original 7 bots used — a deliberate improvement: bar-count
heuristics silently misbehave the moment a timeframe doesn't evenly
divide a day, timestamp-based boundaries don't have that failure mode and
work identically in backtest and live.

CONSECUTIVE-LOSS HALT DESIGN (fixed after a real bug found via Phase 6's
evaluation of Breakout+Retest — see docs/EVALUATION_BREAKOUT_RETEST.md):
the loss counter is NOT reset to 0 when a halt triggers. It resets ONLY
on a win. This matters because the halt only actually blocks a signal
that happens to land inside its cooldown window — on a sparse-signal
timeframe, the next attempt often arrives after the halt has already
expired. The original version reset the counter on every trigger
regardless, so a losing streak that continued past the halt's expiry
would start counting from zero again and "look safe" after exactly
`max_consecutive_losses` losses, even though nothing about the adverse
conditions had changed. Not resetting on trigger means every qualifying
loss re-arms (extends) the halt, so a persistent losing streak stays
continuously halted until an actual win breaks it — not just until the
counter happens to tick back down to zero.
"""

from dataclasses import dataclass, field

import pandas as pd

from cryptobot.risk.position_sizing import calculate_size


@dataclass
class RiskLimits:
    risk_per_trade_pct: float = 0.5
    max_daily_loss_pct: float = 2.0
    max_weekly_loss_pct: float = 5.0
    max_open_positions: int = 1
    max_portfolio_exposure_pct: float = 25.0
    max_position_pct: float = 25.0
    max_consecutive_losses: int = 3
    cooldown_bars: int = 4
    halt_cooldown_hours: int = 24


@dataclass
class RiskManagerState:
    """Exposed read-only-ish snapshot for journaling/logging — not the
    live internal state itself, which RiskManager owns."""
    equity: float
    day_start_equity: float
    week_start_equity: float
    consecutive_losses: int
    halted_until: pd.Timestamp | None
    emergency_shutdown: bool
    open_positions: int
    exposure_pct: float


class RiskManager:
    def __init__(self, limits: RiskLimits, starting_equity: float):
        if starting_equity <= 0:
            raise ValueError("starting_equity must be positive")
        self.limits = limits
        self.equity = starting_equity
        self.day_start_equity = starting_equity
        self.week_start_equity = starting_equity
        self._day_start_date = None
        self._week_start_key = None
        self.consecutive_losses = 0
        self.halted_until: pd.Timestamp | None = None
        self.emergency_shutdown = False
        self.shutdown_reason: str | None = None
        self.open_positions = 0
        self.exposure_pct = 0.0
        self._last_trade_close_bar: int | None = None

    def _roll_day_week_if_needed(self, dt: pd.Timestamp) -> None:
        d = dt.date()
        if self._day_start_date is None or d != self._day_start_date:
            self._day_start_date = d
            self.day_start_equity = self.equity
        iso = dt.isocalendar()
        week_key = (iso.year, iso.week)
        if self._week_start_key is None or week_key != self._week_start_key:
            self._week_start_key = week_key
            self.week_start_equity = self.equity

    def daily_loss_pct(self) -> float:
        if self.day_start_equity <= 0:
            return 0.0
        return max(0.0, (self.day_start_equity - self.equity) / self.day_start_equity * 100)

    def weekly_loss_pct(self) -> float:
        if self.week_start_equity <= 0:
            return 0.0
        return max(0.0, (self.week_start_equity - self.equity) / self.week_start_equity * 100)

    def mark_time(self, dt: pd.Timestamp) -> None:
        """Call once per bar, even with no trade activity, so day/week
        windows roll over correctly regardless of trade frequency."""
        self._roll_day_week_if_needed(dt)

    def can_open_position(self, dt: pd.Timestamp, bar_index: int) -> tuple[bool, str]:
        """Returns (allowed, reason). reason is "" when allowed."""
        self._roll_day_week_if_needed(dt)
        if self.emergency_shutdown:
            return False, "emergency_shutdown"
        if self.halted_until is not None and dt < self.halted_until:
            return False, "circuit_breaker_halt"
        if self.daily_loss_pct() >= self.limits.max_daily_loss_pct:
            return False, "daily_loss_limit"
        if self.weekly_loss_pct() >= self.limits.max_weekly_loss_pct:
            return False, "weekly_loss_limit"
        if self.open_positions >= self.limits.max_open_positions:
            return False, "max_open_positions"
        if self.exposure_pct >= self.limits.max_portfolio_exposure_pct:
            return False, "max_exposure"
        if (self._last_trade_close_bar is not None and
                (bar_index - self._last_trade_close_bar) < self.limits.cooldown_bars):
            return False, "cooldown"
        return True, ""

    def position_size(self, entry_price: float, stop_price: float) -> float:
        return calculate_size(self.equity, self.limits.risk_per_trade_pct,
                               entry_price, stop_price, self.limits.max_position_pct)

    def register_position_opened(self, notional_pct_of_equity: float) -> None:
        self.open_positions += 1
        self.exposure_pct += notional_pct_of_equity

    def register_position_closed(self, pnl: float, dt: pd.Timestamp, bar_index: int,
                                  notional_pct_of_equity: float) -> None:
        self._roll_day_week_if_needed(dt)
        self.equity += pnl
        self.open_positions = max(0, self.open_positions - 1)
        self.exposure_pct = max(0.0, self.exposure_pct - notional_pct_of_equity)
        self._last_trade_close_bar = bar_index

        if pnl <= 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.limits.max_consecutive_losses:
                # Re-arm (extend) the halt on EVERY qualifying loss once at
                # or above threshold, not just the first — see the class
                # docstring's note on why NOT resetting the counter here
                # matters. If we reset to 0 on trigger, a losing streak
                # that continues past the halt's own expiry would start a
                # fresh count from zero and "look safe" again after
                # exactly `max_consecutive_losses` losses, even though the
                # adverse conditions never actually changed — found via
                # Phase 6's evaluation (docs/EVALUATION_BREAKOUT_RETEST.md):
                # an 11-loss streak occurred with only 1 halt rejection
                # recorded, because sparse signals meant most re-triggers
                # never actually landed inside a still-active halt window.
                self.halted_until = dt + pd.Timedelta(hours=self.limits.halt_cooldown_hours)
        else:
            self.consecutive_losses = 0

    def trigger_emergency_shutdown(self, reason: str) -> None:
        """STOP OPENING NEW TRADES (spec §29) — does not force-close
        existing positions; that's the caller's decision, this only gates
        new entries from this point forward."""
        self.emergency_shutdown = True
        self.shutdown_reason = reason

    def snapshot(self) -> RiskManagerState:
        return RiskManagerState(
            equity=self.equity, day_start_equity=self.day_start_equity,
            week_start_equity=self.week_start_equity,
            consecutive_losses=self.consecutive_losses, halted_until=self.halted_until,
            emergency_shutdown=self.emergency_shutdown, open_positions=self.open_positions,
            exposure_pct=self.exposure_pct,
        )
