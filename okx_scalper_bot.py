#!/usr/bin/env python3
"""
OKX Cost-Aware Momentum Scalper

An original design (my own), aimed squarely at the problem that sank the
other high-frequency bot in this repo: on OKX spot, market orders pay
~0.10% taker fee on BOTH entry and exit (~0.20% round trip). A scalper that
fires often on a small edge just feeds the exchange. So instead of trying
to out-signal the fees, this bot refuses to trade at all unless the
CURRENT volatility regime makes the target move comfortably clear the
round-trip cost — a pre-trade "is this worth it" check, not just a
"do I have a signal" check.

Signal: EMA(5/13) momentum cross on a 1m chart, gated by:
  1. Relative volume confirmation ("effort vs result", same idea as the
     other bots here).
  2. A liquidity-hours filter (Europe/US overlap) to avoid thin, choppy
     off-hours action.
  3. THE COST FILTER: expected move (ATR x tp multiple, as a % of price)
     must be >= `min_edge_to_cost_ratio` x round-trip cost (fees +
     slippage). If the achievable target can't clear costs by a healthy
     margin, no trade — no matter how clean the cross looks.

Exit: tight ATR stop/target, plus a short forced-flatten (`max_hold_bars`,
default 10 minutes) — a scalp that hasn't resolved quickly has stopped
being a scalp.

Usage:
    python okx_scalper_bot.py                  # paper mode (default, no real orders)
    python okx_scalper_bot.py --live           # live mode (requires explicit flag)
    python okx_scalper_bot.py --backtest 3000  # backtest last 3000 1m candles (paginated)

Env vars required for --live / --demo:
    OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE

This is a SEPARATE file from the other bots in this repo — own config, own
state/log files, no shared imports. Not validated yet — backtest before
trusting it with money, same as every other bot here.
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, timezone

import ccxt
import pandas as pd
import numpy as np

# ----------------------------- CONFIG -----------------------------
CONFIG = {
    "symbol": "BTC/USDT",
    "timeframe": "1m",          # true scalping timeframe
    "candle_limit": 300,

    # Momentum cross
    "ema_fast": 5,
    "ema_slow": 13,

    # Relative volume ("effort vs result")
    "volume_ma_len": 20,
    "volume_mult": 1.3,

    # Liquidity-hours filter (UTC) — avoid thin off-hours chop
    "session_start_utc": 12,
    "session_end_utc": 21,

    # Risk
    "atr_len": 14,
    "atr_stop_mult": 1.0,
    "atr_tp_mult": 1.5,
    "risk_per_trade_pct": 0.5,   # smaller per-trade risk given higher trade frequency
    "max_position_pct": 25.0,

    # THE COST FILTER — the core idea of this bot.
    # Required ratio of (expected target move, as % of price) to
    # (round-trip fee + slippage, as % of price) before a signal is allowed
    # to fire at all. Refuses trades where even a full win barely clears cost.
    "min_edge_to_cost_ratio": 3.0,

    # Day-trading discipline: a scalp that hasn't resolved quickly isn't one
    "max_hold_bars": 10,         # 10 x 1m = 10 minutes
    "cooldown_bars": 3,

    # Circuit breakers (tighter than the other bots — high frequency means
    # a bad streak compounds faster)
    "daily_loss_limit_pct": 3.0,
    "max_consecutive_losses": 5,
    "halt_cooldown_hours": 4,

    # Volatility spike guard
    "vol_spike_lookback": 20,
    "vol_spike_mult": 2.5,

    # Costs (OKX spot, standard tier; market orders => taker both sides)
    "taker_fee_pct": 0.10,
    "entry_slippage_pct": 0.05,
    "stop_slippage_pct": 0.3,

    "long_only": True,          # spot cannot short; keep True unless using swap

    # Ops
    "poll_seconds": 15,          # tighter poll for a 1m timeframe
    "state_file": "scalper_state.json",
    "log_file": "scalper.log",
}

# ----------------------------- LOGGING -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(CONFIG["log_file"]),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("okx-scalper-bot")


# ----------------------------- INDICATORS -----------------------------
def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    return true_range(df).ewm(alpha=1 / length, adjust=False).mean()


# ----------------------------- SIGNAL ENGINE -----------------------------
def compute_signals(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    d = df.copy()
    if "dt" not in d.columns and "ts" in d.columns:
        d["dt"] = pd.to_datetime(d["ts"], unit="ms", utc=True)

    d["ema_fast"] = ema(d["close"], cfg["ema_fast"])
    d["ema_slow"] = ema(d["close"], cfg["ema_slow"])
    bull = d["ema_fast"] > d["ema_slow"]
    bear = d["ema_fast"] < d["ema_slow"]
    d["bull_cross"] = bull & ~(bull.shift(1).fillna(False))
    d["bear_cross"] = bear & ~(bear.shift(1).fillna(False))

    d["volume_ma"] = d["volume"].rolling(cfg["volume_ma_len"]).mean()
    d["volume_confirm"] = d["volume"] > (d["volume_ma"] * cfg["volume_mult"])

    hour = d["dt"].dt.hour
    d["in_session"] = (hour >= cfg["session_start_utc"]) & (hour < cfg["session_end_utc"])

    d["atr"] = atr(d, cfg["atr_len"])
    d["atr_avg"] = d["atr"].rolling(cfg["vol_spike_lookback"]).mean()
    d["vol_spike"] = d["atr"] > (d["atr_avg"] * cfg["vol_spike_mult"])

    # THE COST FILTER: expected move vs round-trip cost, both as % of price.
    round_trip_cost_pct = 2 * cfg["taker_fee_pct"] + cfg["entry_slippage_pct"]
    d["expected_move_pct"] = (d["atr"] * cfg["atr_tp_mult"] / d["close"]) * 100
    d["edge_ok"] = d["expected_move_pct"] >= (cfg["min_edge_to_cost_ratio"] * round_trip_cost_pct)

    base = d["volume_confirm"].fillna(False) & d["in_session"] & d["edge_ok"] & ~d["vol_spike"].fillna(False)
    d["long_signal"] = d["bull_cross"] & base
    d["short_signal"] = d["bear_cross"] & base
    if cfg.get("long_only", True):
        d["short_signal"] = d["short_signal"] & False

    return d


# ----------------------------- BACKTEST -----------------------------
def backtest(d: pd.DataFrame, cfg: dict):
    fee_pct = cfg["taker_fee_pct"]
    slippage_pct = cfg["entry_slippage_pct"]
    equity = 1000.0
    position = None
    trades = []
    last_stop_bar = -9999
    consec_losses = 0
    total_fees = 0.0
    halt_until_bar = -9999
    day_start_equity = equity
    day_start_bar = 0
    halts = 0
    max_hold = cfg.get("max_hold_bars") or 0

    warmup = max(cfg["ema_slow"], cfg["volume_ma_len"], cfg["atr_len"])
    for i in range(warmup, len(d)):
        row = d.iloc[i]

        if position:
            hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                        else row["high"] >= position["stop"])
            hit_tp = (row["high"] >= position["tp"] if position["side"] == "long"
                      else row["low"] <= position["tp"])
            overstayed = max_hold > 0 and (i - position["opened_bar"]) >= max_hold

            exit_price, reason = None, None
            if hit_stop:
                exit_price, reason = position["stop"], "stop"
            elif hit_tp:
                exit_price, reason = position["tp"], "tp"
            elif overstayed:
                exit_price, reason = row["close"], "time_exit"

            if exit_price:
                if reason == "stop":
                    slip_dir = -1 if position["side"] == "long" else 1
                    exit_price *= (1 + slip_dir * cfg["stop_slippage_pct"] / 100)
                direction = 1 if position["side"] == "long" else -1
                gross = (exit_price - position["entry"]) * direction * position["size"]
                fees = (position["entry"] + exit_price) * position["size"] * (fee_pct / 100)
                pnl = gross - fees
                total_fees += fees
                equity += pnl
                trades.append({
                    "side": position["side"], "entry": position["entry"],
                    "exit": exit_price, "reason": reason, "pnl": pnl, "equity": equity,
                })
                if pnl <= 0:
                    last_stop_bar = i
                    consec_losses += 1
                    if consec_losses >= cfg["max_consecutive_losses"]:
                        halt_until_bar = i + cfg["cooldown_bars"] * 8
                        consec_losses = 0
                else:
                    consec_losses = 0
                position = None

        bars_per_day = max(1, int(24 / _tf_hours(cfg["timeframe"])))
        if i - day_start_bar >= bars_per_day:
            day_start_bar = i
            day_start_equity = equity
        if day_start_equity > 0 and (equity - day_start_equity) / day_start_equity * 100 <= -cfg["daily_loss_limit_pct"]:
            if i > halt_until_bar:
                halts += 1
            halt_until_bar = max(halt_until_bar, i + bars_per_day)

        if position is None and (i - last_stop_bar) >= cfg["cooldown_bars"] and i > halt_until_bar:
            side = None
            if row["long_signal"]:
                side = "long"
            elif row["short_signal"]:
                side = "short"

            if side:
                slip = 1 + (slippage_pct / 100) * (1 if side == "long" else -1)
                entry = row["close"] * slip
                stop_dist = row["atr"] * cfg["atr_stop_mult"]
                tp_dist = row["atr"] * cfg["atr_tp_mult"]

                risk_amt = equity * (cfg["risk_per_trade_pct"] / 100)
                size = risk_amt / stop_dist if stop_dist > 0 else 0
                max_size = (equity * cfg["max_position_pct"] / 100) / entry
                size = min(size, max_size)

                if size > 0:
                    position = {
                        "side": side, "entry": entry, "size": size,
                        "opened_bar": i,
                        "stop": entry - stop_dist if side == "long" else entry + stop_dist,
                        "tp": entry + tp_dist if side == "long" else entry - tp_dist,
                    }

    if not trades:
        return {"trades": 0, "note": "No trades generated with these parameters."}

    t = pd.DataFrame(trades)
    wins = t[t["pnl"] > 0]
    losses = t[t["pnl"] <= 0]
    gross_win = wins["pnl"].sum()
    gross_loss = abs(losses["pnl"].sum())

    peak = t["equity"].cummax()
    max_dd = ((peak - t["equity"]) / peak).max() * 100

    return {
        "trades": len(t),
        "win_rate_pct": round(len(wins) / len(t) * 100, 2),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "net_pnl": round(t["pnl"].sum(), 2),
        "return_pct": round((equity - 1000) / 1000 * 100, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_win": round(wins["pnl"].mean(), 2) if len(wins) else 0,
        "avg_loss": round(losses["pnl"].mean(), 2) if len(losses) else 0,
        "final_equity": round(equity, 2),
        "total_fees_paid": round(total_fees, 2),
        "fees_as_pct_of_gross_win": (round(total_fees / gross_win * 100, 1)
                                     if gross_win > 0 else None),
        "exit_breakdown": t["reason"].value_counts().to_dict(),
        "circuit_breaker_halts": halts,
        "long_trades": int((t["side"] == "long").sum()),
        "short_trades": int((t["side"] == "short").sum()),
    }


def _tf_hours(tf: str) -> float:
    unit = tf[-1]
    n = float(tf[:-1])
    return {"m": n / 60, "h": n, "d": n * 24, "w": n * 168}.get(unit, n)


# ----------------------------- EXCHANGE -----------------------------
def make_exchange(live: bool, demo: bool = False):
    params = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
    if live or demo:
        key = os.getenv("OKX_API_KEY")
        secret = os.getenv("OKX_API_SECRET")
        passphrase = os.getenv("OKX_PASSPHRASE")
        if not all([key, secret, passphrase]):
            log.error("Needs OKX_API_KEY / OKX_API_SECRET / OKX_PASSPHRASE.")
            sys.exit(1)
        params.update({"apiKey": key, "secret": secret, "password": passphrase})

    ex = ccxt.okx(params)
    if demo:
        ex.set_sandbox_mode(True)
        log.info("SANDBOX MODE ENABLED — orders route to OKX demo trading.")
    return ex


def timeframe_to_ms(tf: str) -> int:
    unit = tf[-1]
    n = int(tf[:-1])
    mult = {"m": 60_000, "h": 3_600_000, "d": 86_400_000}.get(unit)
    if mult is None:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return n * mult


def fetch_ohlcv(ex, cfg) -> pd.DataFrame:
    raw = ex.fetch_ohlcv(cfg["symbol"], timeframe=cfg["timeframe"], limit=cfg["candle_limit"])
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


def fetch_ohlcv_paginated(ex, symbol: str, timeframe: str, target_candles: int,
                           limit_per_call: int = 300) -> pd.DataFrame:
    """
    OKX caps a single fetch_ohlcv call at ~300 candles regardless of `limit`.
    Walk BACKWARD from "now": fetch the most recent page, then use the
    oldest timestamp seen so far to request the page before it, repeating
    until target_candles are collected or a page stops moving further back
    (== reached the start of the symbol's listing history on OKX, or —
    relevant on 1m — the start of OKX's retained granular history, which is
    typically much shorter than daily/hourly history).
    """
    tf_ms = timeframe_to_ms(timeframe)
    all_rows = []
    seen_ts = set()
    cursor = None
    while len(all_rows) < target_candles:
        since = None if cursor is None else cursor - limit_per_call * tf_ms
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit_per_call)
        if not batch:
            break
        new_rows = [r for r in batch if r[0] not in seen_ts]
        if not new_rows:
            break
        seen_ts.update(r[0] for r in new_rows)
        all_rows.extend(new_rows)
        oldest_ts = batch[0][0]
        if cursor is not None and oldest_ts >= cursor:
            break
        cursor = oldest_ts
        if len(batch) < limit_per_call:
            break
        time.sleep(ex.rateLimit / 1000)

    df = pd.DataFrame(all_rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset="ts").sort_values("ts").reset_index(drop=True)
    if len(df) > target_candles:
        df = df.iloc[-target_candles:].reset_index(drop=True)
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


# ----------------------------- STATE -----------------------------
def load_state(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"position": None, "last_stop_ts": None, "last_bar_ts": None,
            "consec_losses": 0, "halted_until_ts": None}


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


# ----------------------------- LIVE LOOP -----------------------------
def run_loop(cfg, live: bool, demo: bool = False):
    ex = make_exchange(live, demo)
    state = load_state(cfg["state_file"])
    mode = "LIVE" if live else ("DEMO (OKX sandbox)" if demo else "PAPER (local sim)")
    log.info(f"Starting in {mode} mode — {cfg['symbol']} {cfg['timeframe']} scalper")

    if live or demo:
        try:
            open_orders = ex.fetch_open_orders(cfg["symbol"])
            if open_orders:
                log.warning(f"{len(open_orders)} pre-existing open order(s) found. Review before proceeding.")
        except Exception as e:
            log.error(f"Reconciliation check failed: {e}")

    while True:
        try:
            df = fetch_ohlcv(ex, cfg)
            d = compute_signals(df, cfg)
            row = d.iloc[-2]  # last CLOSED candle
            bar_ts = int(row["ts"])

            if state.get("last_bar_ts") == bar_ts:
                time.sleep(cfg["poll_seconds"])
                continue
            state["last_bar_ts"] = bar_ts

            log.info(
                f"{row['dt']} close={row['close']:.2f} "
                f"cross={'bull' if row['bull_cross'] else 'bear' if row['bear_cross'] else '-'} "
                f"edge_ok={bool(row['edge_ok'])} (move {row['expected_move_pct']:.3f}%) "
                f"L={bool(row['long_signal'])} S={bool(row['short_signal'])}"
            )

            halted_until = state.get("halted_until_ts")
            if halted_until and bar_ts < halted_until:
                log.warning(f"HALTED until {datetime.fromtimestamp(halted_until/1000, tz=timezone.utc)} — skipping entries.")
                save_state(cfg["state_file"], state)
                time.sleep(cfg["poll_seconds"])
                continue

            if bool(row.get("vol_spike", False)):
                log.warning(f"VOLATILITY SPIKE (ATR {row['atr']:.2f} vs avg {row['atr_avg']:.2f}) — no new entries.")

            if state["position"] is None:
                side = "long" if row["long_signal"] else ("short" if row["short_signal"] else None)
                if side:
                    stop_dist = row["atr"] * cfg["atr_stop_mult"]
                    tp_dist = row["atr"] * cfg["atr_tp_mult"]
                    entry = float(row["close"])
                    stop = entry - stop_dist if side == "long" else entry + stop_dist
                    tp = entry + tp_dist if side == "long" else entry - tp_dist

                    balance = 1000.0
                    if live or demo:
                        bal = ex.fetch_balance()
                        balance = bal["total"].get("USDT", 0)
                        if balance <= 0:
                            log.warning("USDT balance is 0. Fund your demo account in the OKX UI.")

                    risk_amt = balance * (cfg["risk_per_trade_pct"] / 100)
                    size = risk_amt / stop_dist if stop_dist > 0 else 0
                    size = min(size, (balance * cfg["max_position_pct"] / 100) / entry)

                    log.info(f"SIGNAL {side.upper()} @ {entry:.2f} | stop {stop:.2f} | tp {tp:.2f} | size {size:.4f}")

                    if live or demo:
                        order = ex.create_order(
                            cfg["symbol"], "market",
                            "buy" if side == "long" else "sell",
                            size,
                        )
                        log.info(f"{'LIVE' if live else 'DEMO'} ORDER PLACED: {order.get('id')}")
                    else:
                        log.info("PAPER MODE — no order sent.")

                    state["position"] = {
                        "side": side, "entry": entry, "stop": stop,
                        "tp": tp, "size": size, "opened_ts": bar_ts,
                    }
            else:
                p = state["position"]
                price = float(row["close"])
                exit_reason = None
                bars_open = (bar_ts - p["opened_ts"]) / timeframe_to_ms(cfg["timeframe"])
                if p["side"] == "long":
                    if row["low"] <= p["stop"]:
                        exit_reason = "stop"
                    elif row["high"] >= p["tp"]:
                        exit_reason = "tp"
                else:
                    if row["high"] >= p["stop"]:
                        exit_reason = "stop"
                    elif row["low"] <= p["tp"]:
                        exit_reason = "tp"
                if not exit_reason and cfg.get("max_hold_bars") and bars_open >= cfg["max_hold_bars"]:
                    exit_reason = "time_exit"

                if exit_reason:
                    log.info(f"EXIT {p['side']} via {exit_reason} @ ~{price:.2f}")
                    if live or demo:
                        ex.create_order(
                            cfg["symbol"], "market",
                            "sell" if p["side"] == "long" else "buy",
                            p["size"],
                        )
                    if exit_reason == "stop":
                        state["last_stop_ts"] = bar_ts
                        state["consec_losses"] = state.get("consec_losses", 0) + 1
                        if state["consec_losses"] >= cfg["max_consecutive_losses"]:
                            halt_ms = cfg["halt_cooldown_hours"] * 3600 * 1000
                            state["halted_until_ts"] = bar_ts + halt_ms
                            state["consec_losses"] = 0
                            log.error(
                                f"CIRCUIT BREAKER: {cfg['max_consecutive_losses']} consecutive losses. "
                                f"Halting {cfg['halt_cooldown_hours']}h."
                            )
                    else:
                        state["consec_losses"] = 0
                    state["position"] = None

            save_state(cfg["state_file"], state)

        except ccxt.NetworkError as e:
            log.warning(f"Network error, retrying: {e}")
        except ccxt.ExchangeError as e:
            log.error(f"Exchange error: {e}")
        except Exception as e:
            log.exception(f"Unexpected error: {e}")

        time.sleep(cfg["poll_seconds"])


# ----------------------------- MAIN -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="place real orders")
    ap.add_argument("--demo", action="store_true", help="OKX demo trading sandbox (virtual funds)")
    ap.add_argument("--allow-shorts", action="store_true", help="enable shorts (requires swap, not spot)")
    ap.add_argument("--backtest", type=int, metavar="N", help="backtest last N candles (paginated)")
    ap.add_argument("--timeframe", type=str, help="override timeframe (default 1m)")
    ap.add_argument("--symbol", type=str, help="override symbol (e.g. BTC/USDT)")
    ap.add_argument("--min-edge-ratio", type=float, help="override required expected-move-to-cost ratio (default 3.0)")
    ap.add_argument("--volume-mult", type=float, help="override relative-volume confirmation multiplier")
    ap.add_argument("--max-hold-bars", type=int, help="override forced flatten bar count (0 disables)")
    args = ap.parse_args()

    cfg = dict(CONFIG)
    if args.timeframe:
        cfg["timeframe"] = args.timeframe
    if args.symbol:
        cfg["symbol"] = args.symbol
    if args.min_edge_ratio is not None:
        cfg["min_edge_to_cost_ratio"] = args.min_edge_ratio
    if args.volume_mult:
        cfg["volume_mult"] = args.volume_mult
    if args.max_hold_bars is not None:
        cfg["max_hold_bars"] = args.max_hold_bars
    if args.allow_shorts:
        cfg["long_only"] = False
        print("WARNING: shorts require OKX swap markets. Spot cannot short.")

    if args.live and args.demo:
        print("Choose --live OR --demo, not both.")
        return

    if args.backtest:
        ex = make_exchange(live=False)
        cfg["candle_limit"] = args.backtest
        df = fetch_ohlcv_paginated(ex, cfg["symbol"], cfg["timeframe"], args.backtest)
        if len(df) < args.backtest:
            print(f"NOTE: requested {args.backtest} candles but only {len(df)} are "
                  f"available from OKX for {cfg['symbol']} {cfg['timeframe']} "
                  f"(reached start of exchange history for this resolution).")
        d = compute_signals(df, cfg)
        res = backtest(d, cfg)
        round_trip_cost_pct = 2 * cfg["taker_fee_pct"] + cfg["entry_slippage_pct"]
        print(f"\n=== BACKTEST: {cfg['symbol']} {cfg['timeframe']} scalper "
              f"({len(df)} candles, {df['dt'].iloc[0]} -> {df['dt'].iloc[-1]}) "
              f"| round-trip cost ~{round_trip_cost_pct:.2f}% | "
              f"min edge ratio {cfg['min_edge_to_cost_ratio']}x ===")
        for k, v in res.items():
            print(f"  {k:<20} {v}")
        print()
        return

    if args.live:
        print("\n*** LIVE MODE — real orders will be placed on OKX. ***")
        if input("Type 'CONFIRM' to continue: ").strip() != "CONFIRM":
            print("Aborted.")
            return

    run_loop(cfg, live=args.live, demo=args.demo)


if __name__ == "__main__":
    main()
