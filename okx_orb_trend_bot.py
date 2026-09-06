#!/usr/bin/env python3
"""
OKX Opening-Range-Breakout + Daily-Trend Day Trading Bot

An original design (my own, not a transcription of any named trader's
strategy), built on lessons from the other bots in this repo:
  - High trade frequency + tight ATR targets get eaten by fees on OKX spot
    taker costs -> this trades AT MOST once per day per symbol.
  - Requiring too many simultaneous conditions makes signals vanishingly
    rare (see okx_ema_rsi_bot.py) -> this uses exactly 3: range breakout,
    daily trend agreement, volume confirmation.
  - Fading the dominant trend tends to lose -> entries only fire in the
    direction the daily EMA(50) already points.

Mechanism (Opening Range Breakout, a long-documented day-trading style
grounded in real market microstructure — early-session volatility as
institutional participants place orders): define each day's range from the
first `range_hours` of the highest-liquidity UTC window, then trade a
breakout of that range later in the same session, with the daily trend as
a directional filter and volume as a conviction filter.

Usage:
    python okx_orb_trend_bot.py                  # paper mode (default, no real orders)
    python okx_orb_trend_bot.py --live           # live mode (requires explicit flag)
    python okx_orb_trend_bot.py --backtest 3000  # backtest last 3000 entry-timeframe candles

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
    "timeframe": "15m",          # entry / opening-range timeframe
    "htf_timeframe": "1d",       # trend-filter timeframe
    "htf_ema_len": 50,
    "htf_lookback_candles": 400, # fixed daily lookback for a stable trend read

    # Opening range definition (UTC) — Europe/US liquidity overlap
    "session_start_utc": 12,
    "range_hours": 1,            # opening range = [12:00, 13:00) UTC
    "session_end_utc": 21,       # force-flatten any open position by here

    # Volume confirmation ("effort vs result")
    "volume_ma_len": 20,
    "volume_mult": 1.2,

    # Risk
    "atr_len": 14,
    "atr_stop_mult": 1.0,        # ATR floor, used only if the range itself is too tight
    "target_r_multiple": 2.0,    # take-profit = 2x the risk distance
    "risk_per_trade_pct": 1.0,
    "max_position_pct": 25.0,

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

    "long_only": True,           # spot cannot short; keep True unless using swap

    # Ops
    "poll_seconds": 60,
    "state_file": "orb_trend_state.json",
    "log_file": "orb_trend.log",
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
log = logging.getLogger("okx-orb-trend-bot")


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
def compute_signals(df_entry: pd.DataFrame, df_htf: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    d = df_entry.copy()
    if "dt" not in d.columns:
        d["dt"] = pd.to_datetime(d["ts"], unit="ms", utc=True)
    d = d.sort_values("ts").reset_index(drop=True)

    d["date"] = d["dt"].dt.date
    hour = d["dt"].dt.hour
    start, dur, end = cfg["session_start_utc"], cfg["range_hours"], cfg["session_end_utc"]

    in_window = (hour >= start) & (hour < start + dur)
    d["post_window"] = hour >= (start + dur)
    d["in_session"] = (hour >= start) & (hour < end)
    d["session_over"] = hour >= end

    # Opening-range high/low: only computed from bars inside the window,
    # then forward-filled for the rest of that day (never crosses day
    # boundaries because of the date groupby). Bars before/during the
    # window see NaN -> no breakout is possible until the range is formed.
    window_high = d["high"].where(in_window)
    window_low = d["low"].where(in_window)
    d["range_high"] = window_high.groupby(d["date"]).cummax()
    d["range_low"] = window_low.groupby(d["date"]).cummin()
    d["range_high"] = d.groupby("date")["range_high"].ffill()
    d["range_low"] = d.groupby("date")["range_low"].ffill()

    d["atr"] = atr(d, cfg["atr_len"])
    d["atr_avg"] = d["atr"].rolling(cfg["vol_spike_lookback"]).mean()
    d["vol_spike"] = d["atr"] > (d["atr_avg"] * cfg["vol_spike_mult"])

    d["volume_ma"] = d["volume"].rolling(cfg["volume_ma_len"]).mean()
    d["volume_confirm"] = d["volume"] > (d["volume_ma"] * cfg["volume_mult"])

    breakout_long = (d["post_window"] & d["in_session"] &
                      (d["close"] > d["range_high"]) &
                      d["volume_confirm"].fillna(False) & ~d["vol_spike"].fillna(False))
    breakout_short = (d["post_window"] & d["in_session"] &
                       (d["close"] < d["range_low"]) &
                       d["volume_confirm"].fillna(False) & ~d["vol_spike"].fillna(False))

    # Daily trend filter, no lookahead: a daily candle opening at T covers
    # [T, T+1d) and isn't knowable until T+1d. Tag with available_at and
    # merge_asof(backward) so an intraday bar only ever sees a daily close
    # that had actually finished printing.
    reg = df_htf.copy()
    reg["ema"] = ema(reg["close"], cfg["htf_ema_len"])
    reg["htf_bull"] = reg["close"] > reg["ema"]
    reg["htf_bear"] = reg["close"] < reg["ema"]
    reg["available_at"] = reg["ts"] + timeframe_to_ms(cfg["htf_timeframe"])
    reg = reg.sort_values("available_at").reset_index(drop=True)

    merged = pd.merge_asof(
        d[["ts"]], reg[["available_at", "htf_bull", "htf_bear"]],
        left_on="ts", right_on="available_at", direction="backward",
    )
    d["htf_bull"] = merged["htf_bull"].fillna(False).values
    d["htf_bear"] = merged["htf_bear"].fillna(False).values

    d["long_signal"] = breakout_long & d["htf_bull"]
    d["short_signal"] = breakout_short & d["htf_bear"]
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
    last_trade_date = None
    consec_losses = 0
    total_fees = 0.0
    halt_until_bar = -9999
    day_start_equity = equity
    day_start_bar = 0
    halts = 0

    warmup = max(cfg["atr_len"], cfg["volume_ma_len"], cfg["vol_spike_lookback"])
    for i in range(warmup, len(d)):
        row = d.iloc[i]

        if position:
            hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                        else row["high"] >= position["stop"])
            hit_tp = (row["high"] >= position["tp"] if position["side"] == "long"
                      else row["low"] <= position["tp"])
            force_flat = bool(row["session_over"])

            exit_price, reason = None, None
            if hit_stop:
                exit_price, reason = position["stop"], "stop"
            elif hit_tp:
                exit_price, reason = position["tp"], "tp"
            elif force_flat:
                exit_price, reason = row["close"], "session_close"

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
                    consec_losses += 1
                    if consec_losses >= cfg["max_consecutive_losses"]:
                        halt_until_bar = i + 96  # ~1 day of 15m bars
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

        if (position is None and row["date"] != last_trade_date and i > halt_until_bar):
            side = None
            if row["long_signal"]:
                side = "long"
            elif row["short_signal"]:
                side = "short"

            if side and pd.notna(row["range_high"]) and pd.notna(row["range_low"]):
                slip = 1 + (slippage_pct / 100) * (1 if side == "long" else -1)
                entry = row["close"] * slip
                atr_floor = row["atr"] * cfg["atr_stop_mult"]

                if side == "long":
                    risk_dist = max(entry - row["range_low"], atr_floor)
                    stop = entry - risk_dist
                else:
                    risk_dist = max(row["range_high"] - entry, atr_floor)
                    stop = entry + risk_dist

                if risk_dist > 0:
                    tp = entry + risk_dist * cfg["target_r_multiple"] if side == "long" \
                        else entry - risk_dist * cfg["target_r_multiple"]

                    risk_amt = equity * (cfg["risk_per_trade_pct"] / 100)
                    size = risk_amt / risk_dist
                    max_size = (equity * cfg["max_position_pct"] / 100) / entry
                    size = min(size, max_size)

                    if size > 0:
                        position = {"side": side, "entry": entry, "size": size,
                                    "stop": stop, "tp": tp}
                        last_trade_date = row["date"]

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


def fetch_ohlcv(ex, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
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
        return {"position": None, "last_trade_date": None, "last_bar_ts": None,
            "consec_losses": 0, "halted_until_ts": None}


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ----------------------------- LIVE LOOP -----------------------------
def run_loop(cfg, live: bool, demo: bool = False):
    ex = make_exchange(live, demo)
    state = load_state(cfg["state_file"])
    mode = "LIVE" if live else ("DEMO (OKX sandbox)" if demo else "PAPER (local sim)")
    log.info(f"Starting in {mode} mode — {cfg['symbol']} {cfg['timeframe']} "
             f"(ORB {cfg['session_start_utc']}:00-{cfg['session_start_utc']+cfg['range_hours']}:00 UTC, "
             f"session ends {cfg['session_end_utc']}:00 UTC)")

    if live or demo:
        try:
            open_orders = ex.fetch_open_orders(cfg["symbol"])
            if open_orders:
                log.warning(f"{len(open_orders)} pre-existing open order(s) found. Review before proceeding.")
        except Exception as e:
            log.error(f"Reconciliation check failed: {e}")

    while True:
        try:
            df_entry = fetch_ohlcv(ex, cfg["symbol"], cfg["timeframe"], limit=300)
            df_htf = fetch_ohlcv(ex, cfg["symbol"], cfg["htf_timeframe"], limit=300)
            d = compute_signals(df_entry, df_htf, cfg)
            row = d.iloc[-2]  # last CLOSED candle
            bar_ts = int(row["ts"])

            if state.get("last_bar_ts") == bar_ts:
                time.sleep(cfg["poll_seconds"])
                continue
            state["last_bar_ts"] = bar_ts

            log.info(
                f"{row['dt']} close={row['close']:.2f} "
                f"range=[{row['range_low']:.2f},{row['range_high']:.2f}] "
                f"trend={'bull' if row['htf_bull'] else 'bear' if row['htf_bear'] else 'flat'} "
                f"L={bool(row['long_signal'])} S={bool(row['short_signal'])}"
            )

            halted_until = state.get("halted_until_ts")
            if halted_until and bar_ts < halted_until:
                log.warning(f"HALTED until {datetime.fromtimestamp(halted_until/1000, tz=timezone.utc)} — skipping entries.")
                save_state(cfg["state_file"], state)
                time.sleep(cfg["poll_seconds"])
                continue

            row_date = str(row["date"])

            if state["position"] is None:
                side = None
                if row_date != state.get("last_trade_date") and pd.notna(row["range_high"]) and pd.notna(row["range_low"]):
                    side = "long" if row["long_signal"] else ("short" if row["short_signal"] else None)
                if side:
                    atr_floor = row["atr"] * cfg["atr_stop_mult"]
                    entry = float(row["close"])
                    if side == "long":
                        risk_dist = max(entry - row["range_low"], atr_floor)
                        stop = entry - risk_dist
                    else:
                        risk_dist = max(row["range_high"] - entry, atr_floor)
                        stop = entry + risk_dist
                    tp = entry + risk_dist * cfg["target_r_multiple"] if side == "long" \
                        else entry - risk_dist * cfg["target_r_multiple"]

                    balance = 1000.0
                    if live or demo:
                        bal = ex.fetch_balance()
                        balance = bal["total"].get("USDT", 0)
                        if balance <= 0:
                            log.warning("USDT balance is 0. Fund your demo account in the OKX UI.")

                    risk_amt = balance * (cfg["risk_per_trade_pct"] / 100)
                    size = risk_amt / risk_dist if risk_dist > 0 else 0
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
                    state["last_trade_date"] = row_date
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
                if not exit_reason and bool(row["session_over"]):
                    exit_reason = "session_close"

                if exit_reason:
                    log.info(f"EXIT {p['side']} via {exit_reason} @ ~{price:.2f}")
                    if live or demo:
                        ex.create_order(
                            cfg["symbol"], "market",
                            "sell" if p["side"] == "long" else "buy",
                            p["size"],
                        )
                    if exit_reason == "stop" or price < p["entry"] if p["side"] == "long" else price > p["entry"]:
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
    ap.add_argument("--backtest", type=int, metavar="N", help="backtest last N entry-timeframe candles (paginated)")
    ap.add_argument("--timeframe", type=str, help="override entry/opening-range timeframe (default 15m)")
    ap.add_argument("--symbol", type=str, help="override symbol (e.g. BTC/USDT)")
    ap.add_argument("--range-hours", type=int, help="override opening-range duration in hours (default 1)")
    ap.add_argument("--session-start", type=int, help="override session/range start hour UTC (default 12)")
    ap.add_argument("--session-end", type=int, help="override forced-flatten hour UTC (default 21)")
    ap.add_argument("--volume-mult", type=float, help="override relative-volume confirmation multiplier")
    args = ap.parse_args()

    cfg = dict(CONFIG)
    if args.timeframe:
        cfg["timeframe"] = args.timeframe
    if args.symbol:
        cfg["symbol"] = args.symbol
    if args.range_hours:
        cfg["range_hours"] = args.range_hours
    if args.session_start is not None:
        cfg["session_start_utc"] = args.session_start
    if args.session_end is not None:
        cfg["session_end_utc"] = args.session_end
    if args.volume_mult:
        cfg["volume_mult"] = args.volume_mult
    if args.allow_shorts:
        cfg["long_only"] = False
        print("WARNING: shorts require OKX swap markets. Spot cannot short.")

    if args.live and args.demo:
        print("Choose --live OR --demo, not both.")
        return

    if args.backtest:
        ex = make_exchange(live=False)
        df_entry = fetch_ohlcv_paginated(ex, cfg["symbol"], cfg["timeframe"], args.backtest)
        if len(df_entry) < args.backtest:
            print(f"NOTE: requested {args.backtest} candles but only {len(df_entry)} are "
                  f"available from OKX for {cfg['symbol']} {cfg['timeframe']} "
                  f"(reached start of exchange history).")
        df_htf = fetch_ohlcv_paginated(ex, cfg["symbol"], cfg["htf_timeframe"], cfg["htf_lookback_candles"])
        d = compute_signals(df_entry, df_htf, cfg)
        res = backtest(d, cfg)
        print(f"\n=== BACKTEST: {cfg['symbol']} {cfg['timeframe']} ORB "
              f"({len(df_entry)} candles, {df_entry['dt'].iloc[0].date()} -> {df_entry['dt'].iloc[-1].date()}) "
              f"| trend filter: {cfg['htf_timeframe']} EMA{cfg['htf_ema_len']} "
              f"({len(df_htf)} candles) ===")
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
