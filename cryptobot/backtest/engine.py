"""
backtest/engine.py — event-driven bar-by-bar backtest engine.

Execution model, deliberately more rigorous than the ad hoc entry-at-
signal-bar's-own-close convention used in this project's earlier 7
standalone bots: a signal computed from bar i's CLOSE (fully known once
bar i has closed) is executed at bar i+1's OPEN, with slippage applied.
You cannot realistically place and fill a market order at the exact close
of the very bar whose close you're using to decide to trade — the
earliest honest fill is the next bar. See tests/test_backtest_engine.py
for a test that specifically exercises a gap between the signal bar's
close and the next bar's open to prove this.

Stop-loss (spec §18): "structure" method uses a caller-supplied per-bar
stop-level column (e.g. a strategy's broken level) with an ATR floor as a
safety minimum (same "wider of structural distance vs ATR floor" pattern
used throughout this project's earlier bots); "atr" method is a plain ATR
multiple.

"trailing_indicator" method (added for "The Forbidden Book" strategy
set): exit is a SIGNAL, not a fixed price — close crossing to the wrong
side of a per-bar indicator column (e.g. ALMA), re-evaluated every bar,
the level itself moving over time rather than being fixed at entry. Most
of that book's strategies use exactly this ("exit kapag nabreak ng candle
ang ALMA... at nagstay sya dun"), which the fixed-distance atr/structure
methods can't faithfully express. Fires with the SAME next-bar-open
discipline as entries: the cross is detected on bar i's close, the
position closes at bar i+1's open, via a `pending_exit` flag on the
position dict, not an immediate same-bar fill (which would assume a fill
at a price you can't yet know is a signal). A hard ATR-floor stop is
still carried underneath, checked every bar, as a safety net the book's
own rules don't specify but this project's risk-management standard
(spec §16) doesn't skip regardless of which strategy is running.

"signal_exit" method: the same next-bar-open-fill, hard-ATR-stop-
underneath mechanics as trailing_indicator, but for exit conditions that
aren't a simple close-vs-line comparison — e.g. FISHBALL's "Fisher curves
down OR crosses below its trigger", a condition about an indicator's own
behavior, not price vs. a level. The caller precomputes an arbitrary
boolean `exit_signal_col` on the strategy dataframe; the engine just
checks it each bar. trailing_indicator is kept as its own method (rather
than replaced by this more general one) because it was already built,
tested, and used before signal_exit's need became clear — both share
the same underlying discipline, just different trigger sources.

Take-profit (spec §19): fixed R-multiple only for the atr/structure
methods; trailing_indicator/signal_exit have no separate take-profit —
their exit rule IS the whole strategy's exit rule, per the book. The spec
lists five TP approaches and says to backtest each — building all five
before any of them has been evaluated even once would repeat the
over-building this project has deliberately avoided elsewhere. Deferred,
not forgotten.

A position still open when the data runs out is force-closed at the last
available bar's close, labeled exit_reason="end_of_data" — NOT silently
dropped. An earlier version of this engine only ever appended a Trade on
exit, so a position that opened near the end of the data and never hit
its stop/target within the remaining bars vanished from the results
entirely: not counted, not reflected in final equity. Caught by
tests/test_backtest_engine.py, not by inspection — see
TestEndOfDataHandling.

KNOWN LIMITATION: tracks at most ONE open position at a time (matching
every one of the 7 standalone bots earlier in this project), even though
RiskManager's max_open_positions could in principle allow more —
concurrent multi-position tracking would need a list-based position
tracker and is deferred, not silently unsupported. Default
max_open_positions is 1 to match this engine's actual behavior.

No look-ahead: the ONLY new temporal decision in this module (every
signal/level column consumed is already lookahead-safe per its own
engine) is the next-bar-open fill above, which if anything makes
execution MORE conservative than assuming same-bar fills, not less.
"""

from dataclasses import dataclass

import pandas as pd

from cryptobot.risk.risk_manager import RiskLimits, RiskManager
from cryptobot.backtest.metrics import Trade, compute_metrics, BacktestResult


@dataclass
class BacktestCosts:
    taker_fee_pct: float = 0.10
    entry_slippage_pct: float = 0.05
    stop_slippage_pct: float = 0.4


@dataclass
class StopTargetConfig:
    method: str = "atr"          # "atr" | "structure" | "trailing_indicator" | "signal_exit"
    atr_col: str = "vlt_atr"
    atr_mult_stop: float = 1.5
    target_r_multiple: float = 2.0
    structure_stop_col: str | None = None  # required if method == "structure"
    trailing_indicator_col: str | None = None  # required if method == "trailing_indicator"
    exit_signal_col: str | None = None  # required if method == "signal_exit"
    # Optional, only meaningful with method=="structure": a per-bar column
    # giving the STRUCTURAL take-profit price (e.g. "recent swing high" for
    # a long) instead of the usual fixed target_r_multiple. Added for the
    # "3-step formula" price-action strategy (structure_target.py), whose
    # own stated exit is "recent highs/lows", not an arbitrary R-multiple —
    # see backtest/engine.py's module docstring for why fixed R-multiple
    # was the only TP approach built until a strategy actually needed a
    # different one. When set, min_rr (if also set) REJECTS the signal
    # (recorded in rejected_signals, not silently skipped) whenever the
    # resulting reward:risk ratio falls below it — the strategy's own
    # explicit selectivity rule, not a backtest-engine embellishment.
    structure_target_col: str | None = None
    min_rr: float | None = None


def _compute_stop(signal_row: pd.Series, entry_price: float, side: str,
                   cfg: StopTargetConfig) -> float:
    atr_val = signal_row.get(cfg.atr_col, None)
    atr_floor = (atr_val * cfg.atr_mult_stop) if atr_val and atr_val > 0 else 0.0

    if cfg.method == "structure":
        level = signal_row.get(cfg.structure_stop_col, None)
        dist = max(abs(entry_price - level), atr_floor) if level is not None and pd.notna(level) else atr_floor
    else:
        dist = atr_floor

    return entry_price - dist if side == "long" else entry_price + dist


def run_backtest(df: pd.DataFrame, long_entry_col: str, short_entry_col: str | None,
                  risk_limits: RiskLimits, stop_target: StopTargetConfig,
                  costs: BacktestCosts = None, starting_equity: float = 1000.0) -> BacktestResult:
    if stop_target.method == "structure" and not stop_target.structure_stop_col:
        raise ValueError("structure_stop_col is required when stop_target.method == 'structure'")
    if stop_target.method == "trailing_indicator" and not stop_target.trailing_indicator_col:
        raise ValueError("trailing_indicator_col is required when stop_target.method == 'trailing_indicator'")
    if stop_target.method == "signal_exit" and not stop_target.exit_signal_col:
        raise ValueError("exit_signal_col is required when stop_target.method == 'signal_exit'")
    costs = costs or BacktestCosts()

    d = df.reset_index(drop=True)
    rm = RiskManager(risk_limits, starting_equity)

    trades: list[Trade] = []
    rejected_signals: list[dict] = []
    equity_points = []
    position = None

    n = len(d)
    for i in range(1, n - 1):  # need i+1 to exist for the next-bar-open fill
        row = d.iloc[i]
        dt = row["dt"]
        rm.mark_time(dt)

        if position is not None:
            exit_price, reason = None, None

            if stop_target.method in ("trailing_indicator", "signal_exit"):
                if position.get("pending_exit"):
                    # The exit condition was detected on the PRIOR bar's
                    # close; fill now, at THIS bar's open — same next-
                    # bar-open discipline as entries, not an immediate
                    # same-bar fill.
                    exit_price = row["open"]
                    reason = stop_target.method
                else:
                    hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                                else row["high"] >= position["stop"])
                    if hit_stop:
                        exit_price, reason = position["stop"], "stop"
                    elif stop_target.method == "trailing_indicator":
                        indicator_val = row.get(stop_target.trailing_indicator_col)
                        if indicator_val is not None and pd.notna(indicator_val):
                            crossed = (row["close"] < indicator_val if position["side"] == "long"
                                       else row["close"] > indicator_val)
                            if crossed:
                                position["pending_exit"] = True
                    else:  # signal_exit
                        if bool(row.get(stop_target.exit_signal_col, False)):
                            position["pending_exit"] = True
            else:
                hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                            else row["high"] >= position["stop"])
                hit_tp = (row["high"] >= position["tp"] if position["side"] == "long"
                          else row["low"] <= position["tp"])
                if hit_stop:
                    exit_price, reason = position["stop"], "stop"
                elif hit_tp:
                    exit_price, reason = position["tp"], "tp"

            if exit_price is not None:
                if reason == "stop":
                    slip_dir = -1 if position["side"] == "long" else 1
                    exit_price = exit_price * (1 + slip_dir * costs.stop_slippage_pct / 100)
                elif reason in ("trailing_indicator", "signal_exit"):
                    slip_dir = -1 if position["side"] == "long" else 1
                    exit_price = exit_price * (1 + slip_dir * costs.entry_slippage_pct / 100)
                direction = 1 if position["side"] == "long" else -1
                gross = (exit_price - position["entry"]) * direction * position["size"]
                fees = (position["entry"] + exit_price) * position["size"] * (costs.taker_fee_pct / 100)
                pnl = gross - fees
                r_multiple = pnl / position["risk_amount"] if position["risk_amount"] > 0 else 0.0

                rm.register_position_closed(pnl, dt, i, position["notional_pct"])
                trades.append(Trade(
                    side=position["side"], entry_dt=position["entry_dt"], exit_dt=dt,
                    entry_price=position["entry"], exit_price=exit_price,
                    stop_price=position["stop"], size=position["size"], pnl=pnl, fees=fees,
                    exit_reason=reason, r_multiple=r_multiple,
                    holding_bars=i - position["entry_bar"],
                ))
                position = None

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

                    stop_price = _compute_stop(row, entry_price, side, stop_target)
                    risk_dist = abs(entry_price - stop_price)
                    if risk_dist > 0:
                        structural_target = (row.get(stop_target.structure_target_col)
                                              if stop_target.structure_target_col else None)
                        has_valid_structural_target = (
                            structural_target is not None and pd.notna(structural_target)
                            and ((side == "long" and structural_target > entry_price)
                                 or (side == "short" and structural_target < entry_price))
                        )
                        if has_valid_structural_target:
                            tp_price = structural_target
                        else:
                            tp_price = (entry_price + risk_dist * stop_target.target_r_multiple if side == "long"
                                        else entry_price - risk_dist * stop_target.target_r_multiple)

                        rr = abs(tp_price - entry_price) / risk_dist
                        if stop_target.min_rr is not None and rr < stop_target.min_rr:
                            rejected_signals.append({"dt": dt, "side": side, "reason": "rr_below_min",
                                                      "rr": rr, "min_rr": stop_target.min_rr})
                        else:
                            size = rm.position_size(entry_price, stop_price)
                            if size > 0:
                                notional_pct = (size * entry_price / rm.equity) * 100
                                rm.register_position_opened(notional_pct)
                                position = {
                                    "side": side, "entry": entry_price, "size": size,
                                    "stop": stop_price, "tp": tp_price, "pending_exit": False,
                                    "risk_amount": rm.equity * (risk_limits.risk_per_trade_pct / 100),
                                    "entry_dt": next_row["dt"], "entry_bar": i + 1,
                                    "notional_pct": notional_pct,
                                }

    # A position still open when the data runs out must not be silently
    # dropped — that would understate fees/risk and leave the equity
    # curve's final value not reflecting it at all. Force-close at the
    # last available bar's close, honestly labeled as such (not a real
    # stop/target fill).
    if position is not None:
        last_row = d.iloc[-1]
        exit_price = last_row["close"]
        direction = 1 if position["side"] == "long" else -1
        gross = (exit_price - position["entry"]) * direction * position["size"]
        fees = (position["entry"] + exit_price) * position["size"] * (costs.taker_fee_pct / 100)
        pnl = gross - fees
        r_multiple = pnl / position["risk_amount"] if position["risk_amount"] > 0 else 0.0
        rm.register_position_closed(pnl, last_row["dt"], n - 1, position["notional_pct"])
        trades.append(Trade(
            side=position["side"], entry_dt=position["entry_dt"], exit_dt=last_row["dt"],
            entry_price=position["entry"], exit_price=exit_price,
            stop_price=position["stop"], size=position["size"], pnl=pnl, fees=fees,
            exit_reason="end_of_data", r_multiple=r_multiple,
            holding_bars=(n - 1) - position["entry_bar"],
        ))
        equity_points.append((last_row["dt"], rm.equity))

    if equity_points:
        equity_curve = pd.Series([e for _, e in equity_points],
                                  index=pd.DatetimeIndex([dtv for dtv, _ in equity_points]))
    else:
        equity_curve = pd.Series(dtype=float)

    result = compute_metrics(trades, equity_curve, starting_equity, total_bars=n)
    result.rejected_signals = rejected_signals
    return result
