"""
Bridges RiskManager's live in-memory state to/from a JSON-serializable
RiskManagerSnapshot, so paper trading's daily/weekly loss limits,
consecutive-loss halt, and exposure tracking behave identically to
backtesting — carried forward correctly across process restarts instead
of resetting every time the check script runs.
"""

from datetime import date

import pandas as pd

from cryptobot.risk.risk_manager import RiskManager, RiskLimits
from cryptobot.paper_trading.state import RiskManagerSnapshot


def snapshot_risk_manager(rm: RiskManager) -> RiskManagerSnapshot:
    return RiskManagerSnapshot(
        equity=rm.equity,
        day_start_equity=rm.day_start_equity,
        week_start_equity=rm.week_start_equity,
        consecutive_losses=rm.consecutive_losses,
        halted_until=rm.halted_until.isoformat() if rm.halted_until is not None else None,
        emergency_shutdown=rm.emergency_shutdown,
        open_positions=rm.open_positions,
        exposure_pct=rm.exposure_pct,
        last_trade_close_bar=rm._last_trade_close_bar,
        day_start_date=rm._day_start_date.isoformat() if rm._day_start_date else None,
        week_start_key=list(rm._week_start_key) if rm._week_start_key else None,
    )


def restore_risk_manager(limits: RiskLimits, snapshot: RiskManagerSnapshot | None,
                          starting_equity: float) -> RiskManager:
    rm = RiskManager(limits, starting_equity)
    if snapshot is None:
        return rm
    rm.equity = snapshot.equity
    rm.day_start_equity = snapshot.day_start_equity
    rm.week_start_equity = snapshot.week_start_equity
    rm.consecutive_losses = snapshot.consecutive_losses
    rm.halted_until = pd.Timestamp(snapshot.halted_until) if snapshot.halted_until else None
    rm.emergency_shutdown = snapshot.emergency_shutdown
    rm.open_positions = snapshot.open_positions
    rm.exposure_pct = snapshot.exposure_pct
    rm._last_trade_close_bar = snapshot.last_trade_close_bar
    rm._day_start_date = date.fromisoformat(snapshot.day_start_date) if snapshot.day_start_date else None
    rm._week_start_key = tuple(snapshot.week_start_key) if snapshot.week_start_key else None
    return rm
