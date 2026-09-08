"""
Exit Rules Engine — run_backtest_with_exit_rules(), the bar-by-bar
simulation loop for `exit_rules.py`'s state machine. Matches
`backtest.engine.run_backtest`'s exact call signature (df,
long_entry_col, short_entry_col, risk_limits, <config>, costs,
starting_equity) so it can be swapped in via `run_walk_forward`'s
`backtest_fn` parameter without any change to the walk-forward/chaining
machinery — one windowing implementation shared by both engines, not a
second copy.

Genuinely different from run_backtest in one structural way: a position
can be PARTIALLY closed (rules 3 and 4) without ending the trade, so
this loop tracks `remaining_size` against an `original_size`/
`risk_amount_total`, and records EACH partial or full close as its own
`Trade` (proportional size, proportional risk_amount for its
r_multiple) — reusing the exact same Trade/BacktestResult dataclasses
and `compute_metrics`, so every aggregation/comparison tool already
built in this project (aggregate(), chained_max_drawdown_pct(), the
walk-forward per-window reports) works unmodified on a multi-slice trade
list.

RiskManager interaction for partial exits, a real design choice not
specified by exit_rules_spec.md (which doesn't address this project's
internal risk-manager bookkeeping): every slice updates `equity` and
`exposure_pct` as it's realized (always accurate, in real time). Only
the FINAL slice that brings a position fully to zero decrements
`open_positions` and updates the consecutive-loss streak — using the
trade's CUMULATIVE pnl across all its slices, not just the final slice's
own pnl, so a trade that took a profitable partial early and a small
loss on the remainder is correctly judged an overall winner (or loser)
by the streak counter, not scored on its last slice alone.
"""

import pandas as pd

from cryptobot.risk.risk_manager import RiskManager, RiskLimits
from cryptobot.backtest.engine import BacktestCosts
from cryptobot.backtest.metrics import Trade, compute_metrics, BacktestResult
from cryptobot.backtest.exit_rules import (
    ExitRulesConfig, initial_stop_price, check_hard_stop, update_ratchet_and_time_tighten,
    check_time_stop_exit, check_partial_profit_take, check_ema8_derisk, check_ema_failed_reclaim,
)


def _settle_slice(rm: RiskManager, dt: pd.Timestamp, bar_index: int, pnl: float,
                   notional_pct: float, is_final: bool, cumulative_pnl: float) -> None:
    rm._roll_day_week_if_needed(dt)
    rm.equity += pnl
    rm.exposure_pct = max(0.0, rm.exposure_pct - notional_pct)
    if is_final:
        rm.open_positions = max(0, rm.open_positions - 1)
        rm._last_trade_close_bar = bar_index
        if cumulative_pnl <= 0:
            rm.consecutive_losses += 1
            if rm.consecutive_losses >= rm.limits.max_consecutive_losses:
                rm.halted_until = dt + pd.Timedelta(hours=rm.limits.halt_cooldown_hours)
        else:
            rm.consecutive_losses = 0


def run_backtest_with_exit_rules(df: pd.DataFrame, long_entry_col: str, short_entry_col: str | None,
                                  risk_limits: RiskLimits, exit_rules_config: ExitRulesConfig,
                                  costs: BacktestCosts = None, starting_equity: float = 1000.0) -> BacktestResult:
    costs = costs or BacktestCosts()
    cfg = exit_rules_config
    d = df.reset_index(drop=True)
    rm = RiskManager(risk_limits, starting_equity)

    trades: list[Trade] = []
    rejected_signals: list[dict] = []
    equity_points = []
    position = None

    n = len(d)
    for i in range(1, n - 1):
        row = d.iloc[i]
        dt = row["dt"]
        rm.mark_time(dt)

        if position is not None:
            position["days_in_trade"] += 1

            def close_slice(exit_price: float, fraction: float, reason: str, is_final: bool):
                size_sold = position["remaining_size"] * fraction
                direction = 1 if position["side"] == "long" else -1
                gross = (exit_price - position["entry"]) * direction * size_sold
                fees = (position["entry"] + exit_price) * size_sold * (costs.taker_fee_pct / 100)
                pnl = gross - fees
                slice_risk_amount = position["risk_amount_total"] * (size_sold / position["original_size"])
                r_multiple = pnl / slice_risk_amount if slice_risk_amount > 0 else 0.0
                position["cumulative_pnl"] += pnl
                trades.append(Trade(
                    side=position["side"], entry_dt=position["entry_dt"], exit_dt=dt,
                    entry_price=position["entry"], exit_price=exit_price, stop_price=position["stop"],
                    size=size_sold, pnl=pnl, fees=fees, exit_reason=reason, r_multiple=r_multiple,
                    holding_bars=i - position["entry_bar"],
                ))
                _settle_slice(rm, dt, i, pnl, position["notional_pct"] * fraction, is_final,
                              position["cumulative_pnl"])
                position["remaining_size"] -= size_sold
                position["notional_pct"] *= (1 - fraction)

            # RULE 1 — hard stop, intrabar, immediate, always checked first.
            action1 = check_hard_stop(position, row)
            if action1 is not None:
                exit_price = position["stop"] * (1 - costs.stop_slippage_pct / 100 * (1 if position["side"] == "long" else -1))
                close_slice(exit_price, 1.0, "hard_stop", is_final=True)
                position = None
            else:
                # Apply any actions QUEUED yesterday (rules 2-5 are detected
                # on a close, filled at the NEXT bar's open) before
                # evaluating anything new today.
                for action in position["pending_actions"]:
                    slip_dir = -1 if position["side"] == "long" else 1
                    fill_price = row["open"] * (1 + slip_dir * costs.entry_slippage_pct / 100)
                    close_slice(fill_price, action.fraction if action.kind == "partial" else 1.0,
                                action.reason, is_final=(action.kind == "full"))
                    if action.kind == "full":
                        position = None
                        break
                if position is not None:
                    position["pending_actions"] = []

                if position is not None:
                    update_ratchet_and_time_tighten(position, row, cfg)

                    new_pending = []
                    action2 = check_time_stop_exit(position, row, cfg)
                    if action2 is not None:
                        new_pending.append(action2)
                    else:
                        action3 = check_partial_profit_take(position, row, cfg)
                        if action3 is not None:
                            new_pending.append(action3)
                        action4 = check_ema8_derisk(position, row, cfg.ema_fast_col, cfg.ema_slow_col, cfg)
                        if action4 is not None:
                            new_pending.append(action4)
                        else:
                            prev_row = d.iloc[i - 1] if i > 0 else None
                            action5 = check_ema_failed_reclaim(position, row, prev_row,
                                                                cfg.ema_fast_col, cfg.ema_slow_col, cfg)
                            if action5 is not None:
                                new_pending.append(action5)
                    position["pending_actions"] = new_pending

        equity_points.append((dt, rm.equity))

        if position is None:
            side = None
            if bool(row.get(long_entry_col, False)):
                side = "long"
            elif short_entry_col and bool(row.get(short_entry_col, False)):
                side = "short"

            if side:
                allowed, reason = rm.can_open_position(dt, i)
                if not allowed:
                    rejected_signals.append({"dt": dt, "side": side, "reason": reason})
                else:
                    next_row = d.iloc[i + 1]
                    slip = 1 + (costs.entry_slippage_pct / 100) * (1 if side == "long" else -1)
                    entry_price = next_row["open"] * slip
                    stop_price = initial_stop_price(entry_price, side, cfg)
                    size = rm.position_size(entry_price, stop_price)
                    if size > 0:
                        notional_pct = (size * entry_price / rm.equity) * 100
                        rm.register_position_opened(notional_pct)
                        position = {
                            "side": side, "entry": entry_price, "original_size": size,
                            "remaining_size": size, "stop": stop_price,
                            "highest_favorable_price": entry_price,
                            "risk_amount_total": rm.equity * (risk_limits.risk_per_trade_pct / 100),
                            "entry_dt": next_row["dt"], "entry_bar": i + 1,
                            "notional_pct": notional_pct,
                            "days_in_trade": 0, "time_stop_tightened": False,
                            "partial_profit_taken": False, "rule4_active": False,
                            "cumulative_pnl": 0.0, "pending_actions": [],
                        }

    if position is not None and position["remaining_size"] > 0:
        last_row = d.iloc[-1]
        exit_price = last_row["close"]
        direction = 1 if position["side"] == "long" else -1
        size_sold = position["remaining_size"]
        gross = (exit_price - position["entry"]) * direction * size_sold
        fees = (position["entry"] + exit_price) * size_sold * (costs.taker_fee_pct / 100)
        pnl = gross - fees
        slice_risk_amount = position["risk_amount_total"] * (size_sold / position["original_size"])
        r_multiple = pnl / slice_risk_amount if slice_risk_amount > 0 else 0.0
        position["cumulative_pnl"] += pnl
        trades.append(Trade(
            side=position["side"], entry_dt=position["entry_dt"], exit_dt=last_row["dt"],
            entry_price=position["entry"], exit_price=exit_price, stop_price=position["stop"],
            size=size_sold, pnl=pnl, fees=fees, exit_reason="end_of_data", r_multiple=r_multiple,
            holding_bars=(n - 1) - position["entry_bar"],
        ))
        _settle_slice(rm, last_row["dt"], n - 1, pnl, position["notional_pct"], True, position["cumulative_pnl"])
        equity_points.append((last_row["dt"], rm.equity))

    if equity_points:
        equity_curve = pd.Series([e for _, e in equity_points],
                                  index=pd.DatetimeIndex([dtv for dtv, _ in equity_points]))
    else:
        equity_curve = pd.Series(dtype=float)

    result = compute_metrics(trades, equity_curve, starting_equity, total_bars=n)
    result.rejected_signals = rejected_signals
    return result
