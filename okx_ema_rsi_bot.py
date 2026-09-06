#!/usr/bin/env python3
"""
OKX EMA Stack + RSI Reversion Day Trading Bot
Trend filter: EMA(20/50/150/200) stack. Entry trigger: RSI(14) crossing into
oversold (<30) within an uptrend = buy; RSI crossing into overbought (>70)
within a downtrend = short ("vice versa"). Exits are ATR-based stop/target,
same risk framework as the other bots in this repo.

This is a systematic reading of a short spec (EMA stack + RSI 30/70,
mirrored both directions) — not a literal transcription of any external
source. Read the docstring below, then backtest before trusting it with
money.

Usage:
    python okx_ema_rsi_bot.py                  # paper mode (default, no real orders)
    python okx_ema_rsi_bot.py --live           # live mode (requires explicit flag)
    python okx_ema_rsi_bot.py --backtest 3000  # backtest last 3000 candles (paginated)

Env vars required for --live / --demo:
    OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE

Core signal logic:
    - EMA stack: ema20 > ema50 > ema150 > ema200 = bullish trend context;
      reverse order = bearish. No trend-strength filter (no ADX) — just
      the stack ordering, as specified.
    - Long entry: bullish stack AND RSI crosses below 30 this bar (buying
      the dip within an established uptrend, not fading a downtrend).
    - Short entry: bearish stack AND RSI crosses above 70 this bar
      (mirrored — shorting the rip within an established downtrend).
      Spot cannot short; requires --allow-shorts + OKX swap markets.
    - RSI crossing back the OTHER way (>70 while long, <30 while short) is
      NOT wired as a separate exit signal here — exits are ATR stop/target
      only, to keep one well-tested exit mechanism rather than inventing an
      untested second one. Say so if you wanted an RSI-based exit instead.

This is a SEPARATE file from okx_trend_bot.py and okx_zeefreaks_bot.py —
own config, own state/log files, no shared imports.
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
    "timeframe": "1h",          # day-trading timeframe
    "candle_limit": 500,

    # EMA stack (trend filter only, as specified — no ADX/strength filter)
    "ema1": 20,
    "ema2": 50,
    "ema3": 150,
    "ema4": 200,

    # RSI entry trigger
    "rsi_len": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,

    # Risk
    "atr_len": 14,
    "atr_stop_mult": 1.5,
    "atr_tp_mult": 2.5,
    "risk_per_trade_pct": 1.0,
    "max_position_pct": 25.0,

    "cooldown_bars": 4,

    # Circuit breakers
    "daily_loss_limit_pct": 5.0,
    "max_consecutive_losses": 3,
    "halt_cooldown_hours": 24,

    # Volatility spike guard
    "vol_spike_lookback": 20,
    "vol_spike_mult": 2.5,

    # Costs (OKX spot, standard tier; market orders => taker both sides)
    "taker_fee_pct": 0.10,
    "entry_slippage_pct": 0.05,
    "stop_slippage_pct": 0.4,

    "long_only": True,          # spot cannot short; keep True unless using swap

    # Ops
    "poll_seconds": 60,
    "state_file": "ema_rsi_state.json",
    "log_file": "ema_rsi.log",
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
log = logging.getLogger("okx-ema-rsi-bot")


# ----------------------------- INDICATORS -----------------------------
def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


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

    d["ema1"] = ema(d["close"], cfg["ema1"])
    d["ema2"] = ema(d["close"], cfg["ema2"])
    d["ema3"] = ema(d["close"], cfg["ema3"])
    d["ema4"] = ema(d["close"], cfg["ema4"])

    d["bull_stack"] = (d["ema1"] > d["ema2"]) & (d["ema2"] > d["ema3"]) & (d["ema3"] > d["ema4"])
    d["bear_stack"] = (d["ema1"] < d["ema2"]) & (d["ema2"] < d["ema3"]) & (d["ema3"] < d["ema4"])

    d["rsi"] = rsi(d["close"], cfg["rsi_len"])
    ob, os_ = cfg["rsi_overbought"], cfg["rsi_oversold"]
    d["rsi_cross_dn_oversold"] = (d["rsi"] < os_) & (d["rsi"].shift(1) >= os_)
    d["rsi_cross_up_overbought"] = (d["rsi"] > ob) & (d["rsi"].shift(1) <= ob)

    d["atr"] = atr(d, cfg["atr_len"])
    d["atr_avg"] = d["atr"].rolling(cfg["vol_spike_lookback"]).mean()
    d["vol_spike"] = d["atr"] > (d["atr_avg"] * cfg["vol_spike_mult"])

    d["long_signal"] = d["bull_stack"] & d["rsi_cross_dn_oversold"] & ~d["vol_spike"].fillna(False)
    d["short_signal"] = d["bear_stack"] & d["rsi_cross_up_overbought"] & ~d["vol_spike"].fillna(False)
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

    warmup = max(cfg["ema4"], cfg["rsi_len"], cfg["atr_len"])
    for i in range(warmup, len(d)):
        row = d.iloc[i]

        if position:
            hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                        else row["high"] >= position["stop"])
            hit_tp = (row["high"] >= position["tp"] if position["side"] == "long"
                      else row["low"] <= position["tp"])

            exit_price, reason = None, None
            if hit_stop:
                exit_price, reason = position["stop"], "stop"
            elif hit_tp:
                exit_price, reason = position["tp"], "tp"

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
                if reason == "stop" and pnl <= 0:
                    last_stop_bar = i
                    consec_losses += 1
                    if consec_losses >= cfg["max_consecutive_losses"]:
                        halt_until_bar = i + cfg["cooldown_bars"] * 4
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
    (== reached the start of the symbol's listing history on OKX).
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
    log.info(f"Starting in {mode} mode — {cfg['symbol']} {cfg['timeframe']}")

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
                f"{row['dt']} close={row['close']:.2f} rsi={row['rsi']:.1f} "
                f"stack={'bull' if row['bull_stack'] else 'bear' if row['bear_stack'] else 'mixed'} "
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
    ap.add_argument("--timeframe", type=str, help="override timeframe (e.g. 1h, 4h, 1d)")
    ap.add_argument("--symbol", type=str, help="override symbol (e.g. BTC/USDT)")
    ap.add_argument("--rsi-oversold", type=float, help="override RSI oversold threshold (default 30)")
    ap.add_argument("--rsi-overbought", type=float, help="override RSI overbought threshold (default 70)")
    args = ap.parse_args()

    cfg = dict(CONFIG)
    if args.timeframe:
        cfg["timeframe"] = args.timeframe
    if args.symbol:
        cfg["symbol"] = args.symbol
    if args.rsi_oversold is not None:
        cfg["rsi_oversold"] = args.rsi_oversold
    if args.rsi_overbought is not None:
        cfg["rsi_overbought"] = args.rsi_overbought
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
                  f"(reached start of exchange history).")
        d = compute_signals(df, cfg)
        res = backtest(d, cfg)
        print(f"\n=== BACKTEST: {cfg['symbol']} {cfg['timeframe']} "
              f"({len(df)} candles, {df['dt'].iloc[0].date()} -> {df['dt'].iloc[-1].date()}) ===")
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
