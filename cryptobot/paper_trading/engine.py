"""
Paper Trading Engine — generic, strategy-agnostic incremental decision
engine. Reuses the EXACT SAME stop/target/RR decision
(backtest.engine.compute_entry_decision) and RiskManager as
backtesting, so paper trading is never a parallel reimplementation that
could silently drift from what was actually backtested — one source of
truth for "what does this stop_target config decide", used by both the
historical batch simulator (backtest/engine.py) and this live
incremental one.

Why run_backtest can't just be reused directly for live decisions: its
loop deliberately skips the LAST bar of whatever data it's given (it
needs bar i+1 to exist for the next-bar-open fill convention) — there's
no "next bar" yet when running in real time. This module implements the
equivalent PER-BAR decision logic incrementally instead: each invocation
looks at exactly the most recently CLOSED candle (a still-forming
candle is explicitly excluded — see `latest_closed_bar`), decides
entry/exit exactly as run_backtest would have on that bar, and fills at
the CURRENT live price rather than a historical "next bar's open" —
because running this promptly after each new candle closes makes "right
now" the live equivalent of "next bar's open".

`last_processed_ts` makes re-running the check script harmless (e.g. a
cron job firing twice, or a manual re-check) — a candle already
processed is never re-evaluated.
"""

from dataclasses import asdict

import pandas as pd

from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig, BacktestCosts, compute_entry_decision
from cryptobot.paper_trading.state import PaperTradingState, PaperPosition, PaperTrade
from cryptobot.paper_trading.risk_bridge import snapshot_risk_manager, restore_risk_manager


def latest_closed_bar(df: pd.DataFrame, timeframe_ms: int, now_ms: int) -> pd.Series | None:
    """The most recent row whose candle has actually finished (ts +
    timeframe_ms <= now). Exchanges commonly include the still-forming
    candle as the last row of a recent-OHLCV fetch — that row must never
    be treated as a closed, decision-worthy bar."""
    closed = df[df["ts"] + timeframe_ms <= now_ms]
    if closed.empty:
        return None
    return closed.iloc[-1]


def _check_exit(state: PaperTradingState, bar: pd.Series, stop_target: StopTargetConfig,
                 costs: BacktestCosts) -> tuple[float, str] | tuple[None, None]:
    pos = state.position
    if stop_target.method in ("trailing_indicator", "signal_exit"):
        if pos.pending_exit:
            return None, stop_target.method  # caller fills at live price, not a historical level
        hit_stop = (bar["low"] <= pos.stop) if pos.side == "long" else (bar["high"] >= pos.stop)
        if hit_stop:
            return pos.stop, "stop"
        if stop_target.method == "trailing_indicator":
            indicator_val = bar.get(stop_target.trailing_indicator_col)
            if indicator_val is not None and pd.notna(indicator_val):
                crossed = (bar["close"] < indicator_val if pos.side == "long"
                           else bar["close"] > indicator_val)
                if crossed:
                    pos.pending_exit = True
        else:
            if bool(bar.get(stop_target.exit_signal_col, False)):
                pos.pending_exit = True
        return None, None
    else:
        hit_stop = (bar["low"] <= pos.stop) if pos.side == "long" else (bar["high"] >= pos.stop)
        hit_tp = (bar["high"] >= pos.tp) if pos.side == "long" else (bar["low"] <= pos.tp)
        if hit_stop:
            return pos.stop, "stop"
        if hit_tp:
            return pos.tp, "tp"
        return None, None


def check_and_update(state: PaperTradingState, signal_df: pd.DataFrame, timeframe_ms: int, now_ms: int,
                      long_col: str, short_col: str | None, stop_target: StopTargetConfig,
                      risk_limits: RiskLimits, live_price: float, live_dt: pd.Timestamp,
                      costs: BacktestCosts = None) -> dict:
    """
    `signal_df` — the strategy's compute_* output on recently-fetched
    OHLCV (MarketDataProvider.get_recent_ohlcv is enough; no full
    paginated history needed once a strategy's indicators have warmed up
    within the fetched window).
    `live_price`/`live_dt` — a FRESH quote, fetched separately from
    signal_df, used as the actual fill price. signal_df's own last row
    is the most recently CLOSED candle (yesterday's close for a daily
    strategy), not itself a fillable "right now" price.

    Returns a dict describing what happened this check, for logging/
    notification — always has an "action" key: "no_closed_bar_yet",
    "already_processed", "none", "entered", "exited", or
    "signal_rejected".
    """
    costs = costs or BacktestCosts()
    bar = latest_closed_bar(signal_df, timeframe_ms, now_ms)
    if bar is None:
        return {"action": "no_closed_bar_yet"}

    if state.last_processed_ts is not None and bar["ts"] <= state.last_processed_ts:
        return {"action": "already_processed", "bar_ts": int(bar["ts"])}

    rm = restore_risk_manager(risk_limits, state.risk, state.starting_equity)
    state.bar_index += 1
    rm.mark_time(bar["dt"])

    result = {"action": "none", "bar_ts": int(bar["ts"]), "bar_dt": str(bar["dt"])}

    if state.position is not None:
        exit_price, reason = _check_exit(state, bar, stop_target, costs)
        if reason is not None:
            fill = live_price if exit_price is None else exit_price
            if reason == "stop":
                slip_dir = -1 if state.position.side == "long" else 1
                fill = fill * (1 + slip_dir * costs.stop_slippage_pct / 100)
            elif reason in ("trailing_indicator", "signal_exit"):
                slip_dir = -1 if state.position.side == "long" else 1
                fill = fill * (1 + slip_dir * costs.entry_slippage_pct / 100)

            pos = state.position
            direction = 1 if pos.side == "long" else -1
            gross = (fill - pos.entry_price) * direction * pos.size
            fees = (pos.entry_price + fill) * pos.size * (costs.taker_fee_pct / 100)
            pnl = gross - fees
            r_multiple = pnl / pos.risk_amount if pos.risk_amount > 0 else 0.0

            rm.register_position_closed(pnl, live_dt, state.bar_index, pos.notional_pct)
            trade = PaperTrade(side=pos.side, entry_dt=pos.entry_dt, exit_dt=str(live_dt),
                                entry_price=pos.entry_price, exit_price=fill, stop_price=pos.stop,
                                size=pos.size, pnl=pnl, fees=fees, exit_reason=reason,
                                r_multiple=r_multiple)
            state.trades.append(trade)
            state.position = None
            result.update({"action": "exited", "trade": asdict(trade)})

    if state.position is None and result["action"] != "exited":
        side = None
        if bool(bar.get(long_col, False)):
            side = "long"
        elif short_col and bool(bar.get(short_col, False)):
            side = "short"

        if side:
            allowed, deny_reason = rm.can_open_position(live_dt, state.bar_index)
            if not allowed:
                result.update({"action": "signal_rejected", "reason": deny_reason, "side": side})
            else:
                slip = 1 + (costs.entry_slippage_pct / 100) * (1 if side == "long" else -1)
                entry_price = live_price * slip
                decision = compute_entry_decision(bar, entry_price, side, stop_target)
                if decision is not None and not decision.rejected:
                    size = rm.position_size(entry_price, decision.stop_price)
                    if size > 0:
                        notional_pct = (size * entry_price / rm.equity) * 100
                        rm.register_position_opened(notional_pct)
                        state.position = PaperPosition(
                            side=side, entry_price=entry_price, entry_dt=str(live_dt),
                            entry_bar_index=state.bar_index, stop=decision.stop_price,
                            tp=decision.tp_price, size=size,
                            risk_amount=rm.equity * (risk_limits.risk_per_trade_pct / 100),
                            notional_pct=notional_pct,
                        )
                        result.update({"action": "entered", "side": side, "entry_price": entry_price,
                                       "stop": decision.stop_price, "tp": decision.tp_price, "size": size})
                elif decision is not None and decision.rejected:
                    result.update({"action": "signal_rejected", "reason": decision.reject_reason,
                                   "side": side, "rr": decision.rr})

    state.last_processed_ts = int(bar["ts"])
    state.risk = snapshot_risk_manager(rm)
    return result
