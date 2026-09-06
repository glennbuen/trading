#!/usr/bin/env python3
"""
OKX Trend Bot — EMA Stack + RSI/MACD Cross + ADX Regime Filter
Mirrors the Pine Script v2 logic for 24/7 VPS execution.

Usage:
    python okx_trend_bot.py                 # paper mode (default, no real orders)
    python okx_trend_bot.py --live          # live mode (requires explicit flag)
    python okx_trend_bot.py --backtest 720  # backtest last 720 candles

Env vars required for --live:
    OKX_API_KEY, OKX_API_SECRET, OKX_PASSPHRASE
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
try:
    import requests
except ImportError:
    requests = None

# ----------------------------- CONFIG -----------------------------
CONFIG = {
    "symbol": "BTC/USDT",
    "timeframe": "1d",          # BTC daily: best liquidity, least noise
    "candle_limit": 500,

    # EMAs
    "ema_fast": 20,
    "ema_mid": 50,
    "ema_slow": 150,
    "ema_trend": 200,

    # Momentum
    "rsi_len": 14,
    "rsi_mid": 50,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "max_trigger_bars": 2,
    # "strict"  = BOTH RSI cross AND MACD cross within max_trigger_bars (very few signals)
    # "relaxed" = MACD cross is the trigger, RSI>50 is a standing confirmation (recommended)
    "trigger_mode": "relaxed",

    # Regime filter
    "adx_len": 14,
    "adx_threshold": 25,
    "require_adx_rising": True,

    # Risk
    "atr_len": 14,
    "atr_stop_mult": 2.5,   # wider stop = fewer noise stop-outs
    "atr_tp_mult": 5.0,     # keep R:R at 2:1 with the wider stop
    "atr_floor_pct": 0.3,
    "risk_per_trade_pct": 1.0,   # % of equity risked per trade
    "max_position_pct": 25.0,    # hard cap on position size vs equity

    # Cooldown
    "cooldown_bars": 6,

    # --- CIRCUIT BREAKERS (crash protection) ---
    "daily_loss_limit_pct": 5.0,      # halt if equity drops this % in 24h
    "max_consecutive_losses": 3,      # halt after N stop-outs in a row
    "halt_cooldown_hours": 24,        # how long a halt lasts

    # Volatility spike guard: skip entries when ATR blows out vs its own average
    "vol_spike_lookback": 20,
    "vol_spike_mult": 2.5,            # ATR > 2.5x its 20-bar avg = no new entries

    # Slippage realism: assume stops fill this much worse than the trigger price
    "stop_slippage_pct": 0.4,         # crash-scenario slippage on stop fills

    # --- COSTS (OKX spot, standard tier) ---
    # Bot uses MARKET orders => taker fee applies on BOTH entry and exit.
    "taker_fee_pct": 0.10,            # ~0.10% per side = ~0.20% round trip
    "entry_slippage_pct": 0.05,       # normal-conditions slippage on entry

    # --- TRAILING STOP (Chandelier-style) ---
    # "fixed"    = exit at atr_tp_mult (original behavior)
    # "trailing" = ratchet stop up behind the highest close since entry
    # "hybrid"   = take partial at target, trail the rest
    "exit_mode": "trailing",
    "trail_atr_mult": 2.5,            # stop trails this far behind peak
    "trail_activate_atr": 1.0,        # only start trailing after +1 ATR profit
    "hybrid_partial_pct": 50,         # % of position closed at target in hybrid mode

    # --- VOLUME CONFIRMATION (Wyckoff / Darvas / Zeefreaks) ---
    # "Effort vs result": a breakout on weak volume is hollow.
    # Default OFF - backtest both ways before trusting it.
    "use_volume_filter": False,
    "volume_ma_len": 20,
    "volume_mult": 1.0,               # signal-candle volume must exceed this x the average

    # --- OSCILLATOR MODE (no trend filter) ---
    # "trend"      = EMA stack + ADX required (default, selective)
    # "oscillator" = RSI + MACD + Stochastic only (more trades, no trend context)
    # "trend"      = EMA stack + ADX (trend-following, enters late)
    # "oscillator" = RSI/MACD/Stoch momentum, no trend filter
    # "dip"        = buy oversold, NO trend filter (catching falling knives)
    # "pullback"   = buy oversold ONLY inside an established uptrend (recommended)
    "signal_mode": "trend",
    "rsi_oversold": 30,
    "rsi_overbought": 70,

    # --- TRIPLE SUPERTREND (community-validated: 60 crypto backtests, avg PF 1.2) ---
    "st1_period": 10, "st1_mult": 1.0,
    "st2_period": 11, "st2_mult": 2.0,
    "st3_period": 12, "st3_mult": 3.0,
    # IMPROVEMENT 1: 2-of-3 agreement instead of 3-of-3 (3/3 over-stacks)
    "st_min_agree": 2,
    # IMPROVEMENT 2: slowest SuperTrend acts as the trend filter, replacing the
    # redundant EMA stack (SuperTrend already encodes trend direction)
    "st_use_ema_stack": False,
    # IMPROVEMENT 3: allow alignment within a window, not one exact bar
    "st_align_window": 3,
    # IMPROVEMENT 4: session filter - only trade high-liquidity hours (UTC)
    # 12:00-21:00 UTC = Europe afternoon + US session overlap
    "use_breakeven_stop": True,   # IMPROVEMENT 5: stop to breakeven at +1R
    # "minimal": ONLY SuperTrend (trend timing) + VWAP (participation).
    # No EMA stack, no RSI, no MACD, no Stochastic, no ADX.
    "signal_mode_minimal": False,

    # --- WILDCARD: volatility-adaptive SuperTrend multiplier ---
    # Instead of a fixed ATR multiplier, widen the band when recent volatility
    # is elevated (chop/expansion) and tighten it when volatility is calm
    # (clean trend). Documented result on this idea: ~58% win rate, 3.2
    # profit factor, ~60% fewer false signals in choppy stretches.
    # Fully backtestable - no live-only dependency.
    "use_adaptive_supertrend": False,
    "adaptive_smooth_len": 5,          # smooth the percentile rank (anti-jitter)
    # VWAP standard-deviation bands: measure HOW FAR from value, not just side
    "use_vwap_bands": False,
    "vwap_band_std": 1.0,              # long requires close > vwap + N*std
    "adaptive_atr_lookback": 100,      # window to rank current ATR against
    "adaptive_mult_low": 1.5,          # multiplier when ATR is in a calm percentile
    "adaptive_mult_high": 4.0,         # multiplier when ATR is in a volatile percentile

    "use_mtf": False,
    "mtf_regime_tf": "1h",
    "mtf_entry_tf": "15m",
    "mtf_regime_limit": 500,
    "mtf_entry_limit": 1500,

    "use_vwap_filter": False,
    "vwap_reset_hours": 24,

    "use_session_filter": True,
    "session_start_utc": 12,
    "session_end_utc": 21,
    "stoch_k": 14,
    "stoch_d": 3,
    "stoch_oversold": 20,
    "stoch_overbought": 80,

    "long_only": True,                # spot cannot short; keep True unless using swap

    # Ops
    "poll_seconds": 60,
    "state_file": "bot_state.json",
    "log_file": "bot.log",
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
log = logging.getLogger("okx-bot")


# ----------------------------- INDICATORS -----------------------------
def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder smoothing
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def macd(series: pd.Series, fast: int, slow: int, signal: int):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line


def adaptive_multiplier(df: pd.DataFrame, cfg: dict, period: int) -> pd.Series:
    """
    Rank current ATR against its own recent history (percentile 0-1), then
    map that percentile onto a multiplier range: calm markets get a tight
    multiplier (fast to react), volatile/choppy markets get a wide one
    (fewer false flips from noise).
    """
    atr_val = atr(df, period)
    lookback = cfg["adaptive_atr_lookback"]
    pct_rank = atr_val.rolling(lookback).apply(
        lambda x: (x < x.iloc[-1]).sum() / len(x) if len(x) > 0 else 0.5, raw=False
    ).fillna(0.5)
    smooth = cfg.get("adaptive_smooth_len", 1)
    if smooth > 1:
        pct_rank = pct_rank.rolling(smooth, min_periods=1).mean()
    lo, hi = cfg["adaptive_mult_low"], cfg["adaptive_mult_high"]
    return lo + pct_rank * (hi - lo)


def supertrend(df: pd.DataFrame, period: int, multiplier: float):
    """Returns (supertrend_line, direction) where direction: 1=up, -1=down."""
    atr_val = atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper = hl2 + multiplier * atr_val
    lower = hl2 - multiplier * atr_val

    st = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    st.iloc[0] = upper.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, len(df)):
        if df["close"].iloc[i-1] > st.iloc[i-1]:
            cur_lower = max(lower.iloc[i], st.iloc[i-1]) if direction.iloc[i-1] == 1 else lower.iloc[i]
        else:
            cur_lower = lower.iloc[i]
        if df["close"].iloc[i-1] < st.iloc[i-1]:
            cur_upper = min(upper.iloc[i], st.iloc[i-1]) if direction.iloc[i-1] == -1 else upper.iloc[i]
        else:
            cur_upper = upper.iloc[i]

        if df["close"].iloc[i] > cur_upper:
            direction.iloc[i] = 1
        elif df["close"].iloc[i] < cur_lower:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]

        st.iloc[i] = cur_lower if direction.iloc[i] == 1 else cur_upper

    return st, direction


def supertrend_with_series_mult(df: pd.DataFrame, period: int, multiplier: pd.Series):
    """SuperTrend where the ATR multiplier varies per bar (adaptive version)."""
    atr_val = atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper = hl2 + multiplier * atr_val
    lower = hl2 - multiplier * atr_val

    st = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    st.iloc[0] = upper.iloc[0]
    direction.iloc[0] = 1

    for i in range(1, len(df)):
        if df["close"].iloc[i-1] > st.iloc[i-1]:
            cur_lower = max(lower.iloc[i], st.iloc[i-1]) if direction.iloc[i-1] == 1 else lower.iloc[i]
        else:
            cur_lower = lower.iloc[i]
        if df["close"].iloc[i-1] < st.iloc[i-1]:
            cur_upper = min(upper.iloc[i], st.iloc[i-1]) if direction.iloc[i-1] == -1 else upper.iloc[i]
        else:
            cur_upper = upper.iloc[i]

        if df["close"].iloc[i] > cur_upper:
            direction.iloc[i] = 1
        elif df["close"].iloc[i] < cur_lower:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]

        st.iloc[i] = cur_lower if direction.iloc[i] == 1 else cur_upper

    return st, direction


def stoch(df: pd.DataFrame, k_len: int = 14, d_len: int = 3):
    """Stochastic oscillator %K and %D."""
    low_n = df["low"].rolling(k_len).min()
    high_n = df["high"].rolling(k_len).max()
    k = 100 * (df["close"] - low_n) / (high_n - low_n).replace(0, np.nan)
    k = k.fillna(50)
    return k.rolling(d_len).mean(), k.rolling(d_len).mean().rolling(d_len).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    return true_range(df).ewm(alpha=1 / length, adjust=False).mean()


def adx(df: pd.DataFrame, length: int) -> pd.Series:
    """Wilder's ADX."""
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = true_range(df)
    atr_w = tr.ewm(alpha=1 / length, adjust=False).mean()

    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / length, adjust=False).mean() / atr_w.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / length, adjust=False).mean() / atr_w.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / length, adjust=False).mean().fillna(0)


def get_fear_greed_index(cache_file: str) -> int:
    """
    Fetch the Fear & Greed Index (0-100). Cached for 1 hour since it's a
    daily-updated value - no point hitting the API every poll cycle.
    Returns 50 (neutral) if unreachable, so the filter fails open rather
    than blocking all trades on a network hiccup.
    """
    try:
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
            if time.time() - cached.get("fetched_at", 0) < 3600:
                return cached["value"]
    except (json.JSONDecodeError, KeyError, OSError):
        pass

    if requests is None:
        return 50

    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        resp.raise_for_status()
        value = int(resp.json()["data"][0]["value"])
        with open(cache_file, "w") as f:
            json.dump({"value": value, "fetched_at": time.time()}, f)
        return value
    except Exception as e:
        log.warning(f"Fear & Greed fetch failed ({e}), treating as neutral (50)")
        return 50


def vwap_bands(df: pd.DataFrame, vwap: pd.Series, reset_hours: int = 24, n_std: float = 1.0):
    """Standard deviation bands around VWAP, computed within each reset bucket."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    if "dt" in df.columns:
        dt = pd.to_datetime(df["dt"], utc=True)
        bucket = (dt.astype("int64") // (reset_hours * 3600 * 10**9))
    else:
        bucket = pd.Series(np.arange(len(df)) // max(1, reset_hours), index=df.index)
    dev = (typical - vwap) ** 2
    weighted_var = (dev * df["volume"]).groupby(bucket).cumsum() / \
                   df["volume"].groupby(bucket).cumsum().replace(0, np.nan)
    std = np.sqrt(weighted_var).ffill().fillna(0)
    return vwap + n_std * std, vwap - n_std * std


def rolling_vwap(df: pd.DataFrame, reset_hours: int = 24) -> pd.Series:
    """VWAP that resets every `reset_hours` (24h default for a 24/7 market)."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    pv = typical * df["volume"]
    # Group into reset-hour buckets using row position as a proxy when no dt.
    if "dt" in df.columns:
        dt = pd.to_datetime(df["dt"], utc=True)
        bucket = (dt.astype("int64") // (reset_hours * 3600 * 10**9))
    else:
        bucket = np.arange(len(df)) // max(1, reset_hours)
    cum_pv = pv.groupby(bucket).cumsum()
    cum_vol = df["volume"].groupby(bucket).cumsum().replace(0, np.nan)
    return (cum_pv / cum_vol).ffill()


def bars_since(cond: pd.Series) -> pd.Series:
    """Bars since condition was last True. Large number if never."""
    idx = np.arange(len(cond))
    last_true = np.where(cond.values, idx, np.nan)
    last_true = pd.Series(last_true).ffill().values
    return pd.Series(idx - last_true, index=cond.index).fillna(9999)


# ----------------------------- SIGNAL ENGINE -----------------------------
def compute_signals(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    d = df.copy()
    if "dt" not in d.columns and "ts" in d.columns:
        try:
            d["dt"] = pd.to_datetime(d["ts"], unit="ms", utc=True)
        except (ValueError, TypeError):
            pass

    d["ema_fast"] = ema(d["close"], cfg["ema_fast"])
    d["ema_mid"] = ema(d["close"], cfg["ema_mid"])
    d["ema_slow"] = ema(d["close"], cfg["ema_slow"])
    d["ema_trend"] = ema(d["close"], cfg["ema_trend"])

    d["rsi"] = rsi(d["close"], cfg["rsi_len"])
    d["macd"], d["macd_sig"] = macd(
        d["close"], cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])

    d["atr"] = atr(d, cfg["atr_len"])
    d["atr_pct"] = (d["atr"] / d["close"]) * 100
    d["adx"] = adx(d, cfg["adx_len"])
    d["adx_rising"] = d["adx"] > d["adx"].shift(1)

    # EMA stack
    d["bull_stack"] = ((d["ema_fast"] > d["ema_mid"]) &
                       (d["ema_mid"] > d["ema_slow"]) &
                       (d["ema_slow"] > d["ema_trend"]))
    d["bear_stack"] = ((d["ema_fast"] < d["ema_mid"]) &
                       (d["ema_mid"] < d["ema_slow"]) &
                       (d["ema_slow"] < d["ema_trend"]))

    # Cross events (trigger, not standing state)
    m = cfg["rsi_mid"]
    d["rsi_cross_up"] = (d["rsi"] > m) & (d["rsi"].shift(1) <= m)
    d["rsi_cross_dn"] = (d["rsi"] < m) & (d["rsi"].shift(1) >= m)
    d["macd_cross_up"] = (d["macd"] > d["macd_sig"]) & (d["macd"].shift(1) <= d["macd_sig"].shift(1))
    d["macd_cross_dn"] = (d["macd"] < d["macd_sig"]) & (d["macd"].shift(1) >= d["macd_sig"].shift(1))

    mtb = cfg["max_trigger_bars"]
    if cfg.get("trigger_mode", "relaxed") == "strict":
        # Both crosses must occur within mtb bars of each other.
        d["long_trigger"] = (bars_since(d["rsi_cross_up"]) <= mtb) & (bars_since(d["macd_cross_up"]) <= mtb)
        d["short_trigger"] = (bars_since(d["rsi_cross_dn"]) <= mtb) & (bars_since(d["macd_cross_dn"]) <= mtb)
    else:
        # MACD cross is the timing trigger; RSI acts as a standing directional confirmation.
        d["long_trigger"] = d["macd_cross_up"] & (d["rsi"] > cfg["rsi_mid"])
        d["short_trigger"] = d["macd_cross_dn"] & (d["rsi"] < cfg["rsi_mid"])

    # Filters
    # Volatility spike guard: ATR far above its own recent average = cascade conditions
    d["atr_avg"] = d["atr"].rolling(cfg["vol_spike_lookback"]).mean()
    d["vol_spike"] = d["atr"] > (d["atr_avg"] * cfg["vol_spike_mult"])

    d["vol_ok"] = (d["atr_pct"] >= cfg["atr_floor_pct"]) & (~d["vol_spike"].fillna(False))

    d["vwap"] = rolling_vwap(d, cfg.get("vwap_reset_hours", 24))
    d["above_vwap"] = d["close"] > d["vwap"]
    d["below_vwap"] = d["close"] < d["vwap"]

    # Volume confirmation: is there real participation behind this move?
    d["volume_ma"] = d["volume"].rolling(cfg["volume_ma_len"]).mean()
    d["volume_confirm"] = d["volume"] > (d["volume_ma"] * cfg["volume_mult"])
    if cfg.get("use_volume_filter", False):
        d["vol_ok"] = d["vol_ok"] & d["volume_confirm"].fillna(False)
    d["regime_ok"] = d["adx"] >= cfg["adx_threshold"]
    if cfg["require_adx_rising"]:
        d["regime_ok"] = d["regime_ok"] & d["adx_rising"]

    d["stoch_k"], d["stoch_d"] = stoch(d, cfg["stoch_k"], cfg["stoch_d"])
    d["stoch_cross_up"] = (d["stoch_k"] > d["stoch_d"]) & (d["stoch_k"].shift(1) <= d["stoch_d"].shift(1))
    d["stoch_cross_dn"] = (d["stoch_k"] < d["stoch_d"]) & (d["stoch_k"].shift(1) >= d["stoch_d"].shift(1))

    mode = cfg.get("signal_mode", "trend")

    if cfg.get("signal_mode_minimal", False):
        if cfg.get("use_adaptive_supertrend", False):
            adaptive_mult = adaptive_multiplier(d, cfg, cfg["st2_period"])
            # supertrend() takes a scalar multiplier; run it per-bar-consistent
            # by using the median adaptive multiplier as a practical middle
            # ground, since true per-bar-varying bands require a custom loop.
            _, dir1 = supertrend_with_series_mult(d, cfg["st2_period"], adaptive_mult)
        else:
            _, dir1 = supertrend(d, cfg["st2_period"], cfg["st2_mult"])
        d["st_dir"] = dir1
        d["vwap"] = rolling_vwap(d, cfg.get("vwap_reset_hours", 24))

        flip_up = (dir1 == 1) & (dir1.shift(1) != 1)
        flip_dn = (dir1 == -1) & (dir1.shift(1) != -1)

        if cfg.get("use_vwap_bands", False):
            upper_b, lower_b = vwap_bands(d, d["vwap"], cfg.get("vwap_reset_hours", 24),
                                          cfg["vwap_band_std"])
            d["vwap_upper"], d["vwap_lower"] = upper_b, lower_b
            vwap_long_ok = d["close"] > upper_b
            vwap_short_ok = d["close"] < lower_b
        else:
            vwap_long_ok = d["close"] > d["vwap"]
            vwap_short_ok = d["close"] < d["vwap"]

        d["long_signal"] = flip_up & vwap_long_ok & d["vol_ok"]
        d["short_signal"] = flip_dn & vwap_short_ok & d["vol_ok"]
        if cfg.get("long_only", True):
            d["short_signal"] = d["short_signal"] & False
        return d

    if mode == "supertrend":
        _, dir1 = supertrend(d, cfg["st1_period"], cfg["st1_mult"])
        _, dir2 = supertrend(d, cfg["st2_period"], cfg["st2_mult"])
        _, dir3 = supertrend(d, cfg["st3_period"], cfg["st3_mult"])
        d["st_dir1"], d["st_dir2"], d["st_dir3"] = dir1, dir2, dir3

        # IMPROVEMENT 1: count agreement rather than demanding unanimity
        bull_votes = (dir1 == 1).astype(int) + (dir2 == 1).astype(int) + (dir3 == 1).astype(int)
        bear_votes = (dir1 == -1).astype(int) + (dir2 == -1).astype(int) + (dir3 == -1).astype(int)
        d["st_bull_votes"], d["st_bear_votes"] = bull_votes, bear_votes

        min_agree = cfg["st_min_agree"]
        bull_ok = bull_votes >= min_agree
        bear_ok = bear_votes >= min_agree

        # IMPROVEMENT 2: slowest SuperTrend (st3) is the trend filter
        bull_ok = bull_ok & (dir3 == 1)
        bear_ok = bear_ok & (dir3 == -1)

        # IMPROVEMENT 3: fire within a window after alignment forms
        w = cfg["st_align_window"]
        fresh_up = bull_ok & ~(bull_ok.shift(1).fillna(False))
        fresh_dn = bear_ok & ~(bear_ok.shift(1).fillna(False))
        d["st_long_trig"] = (bars_since(fresh_up) < w) & bull_ok
        d["st_short_trig"] = (bars_since(fresh_dn) < w) & bear_ok

        long_ok = d["st_long_trig"] & d["regime_ok"] & d["vol_ok"]
        short_ok = d["st_short_trig"] & d["regime_ok"] & d["vol_ok"]

        if cfg.get("st_use_ema_stack", False):
            long_ok = long_ok & d["bull_stack"]
            short_ok = short_ok & d["bear_stack"]

        # IMPROVEMENT 4: session filter
        if cfg.get("use_session_filter", False) and "dt" in d.columns:
            hr = pd.to_datetime(d["dt"], utc=True).dt.hour
            in_session = (hr >= cfg["session_start_utc"]) & (hr < cfg["session_end_utc"])
            d["in_session"] = in_session
            long_ok = long_ok & in_session
            short_ok = short_ok & in_session

        d["long_signal"] = long_ok
        d["short_signal"] = short_ok
        if cfg.get("long_only", True):
            d["short_signal"] = d["short_signal"] & False
        return d

    # Oversold conditions
    d["oversold"] = ((d["rsi"] < cfg["rsi_oversold"]) &
                     (d["stoch_k"] < cfg["stoch_oversold"]) &
                     (d["macd"] < d["macd"].rolling(50).quantile(0.25)))
    d["overbought"] = ((d["rsi"] > cfg["rsi_overbought"]) &
                       (d["stoch_k"] > cfg["stoch_overbought"]) &
                       (d["macd"] > d["macd"].rolling(50).quantile(0.75)))
    # Require a turn-up, not just "still falling"
    d["oversold_turn"] = d["oversold"].shift(1).fillna(False) & (d["stoch_k"] > d["stoch_k"].shift(1))
    d["overbought_turn"] = d["overbought"].shift(1).fillna(False) & (d["stoch_k"] < d["stoch_k"].shift(1))

    if mode == "dip":
        # Pure mean reversion. No trend context. Dangerous.
        d["long_signal"] = d["oversold_turn"] & d["vol_ok"]
        d["short_signal"] = d["overbought_turn"] & d["vol_ok"]
    elif mode == "pullback":
        # Buy dips ONLY within an established uptrend.
        d["long_signal"] = d["bull_stack"] & d["oversold_turn"] & d["vol_ok"]
        d["short_signal"] = d["bear_stack"] & d["overbought_turn"] & d["vol_ok"]
    elif mode == "oscillator":
        # No EMA stack, no ADX. Pure momentum.
        d["long_signal"] = (d["macd_cross_up"] & (d["rsi"] > cfg["rsi_mid"])
                            & (d["stoch_k"] < cfg["stoch_overbought"]) & d["vol_ok"])
        d["short_signal"] = (d["macd_cross_dn"] & (d["rsi"] < cfg["rsi_mid"])
                             & (d["stoch_k"] > cfg["stoch_oversold"]) & d["vol_ok"])
    else:
        d["long_signal"] = d["bull_stack"] & d["long_trigger"] & d["vol_ok"] & d["regime_ok"]
        d["short_signal"] = d["bear_stack"] & d["short_trigger"] & d["vol_ok"] & d["regime_ok"]
    if cfg.get("long_only", True):
        d["short_signal"] = d["short_signal"] & False

    if cfg.get("use_vwap_filter", False) and "long_signal" in d.columns:
        d["long_signal"] = d["long_signal"] & d["above_vwap"]
        d["short_signal"] = d["short_signal"] & d["below_vwap"]

    return d


# ----------------------------- BACKTEST -----------------------------
def backtest(d: pd.DataFrame, cfg: dict):
    fee_pct = cfg["taker_fee_pct"]
    slippage_pct = cfg["entry_slippage_pct"]
    """Bar-by-bar. Stop checked before TP on the same bar (conservative)."""
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

    for i in range(cfg["ema_trend"], len(d)):
        row = d.iloc[i]

        # --- manage open position ---
        if position:
            mode = cfg.get("exit_mode", "fixed")

            # IMPROVEMENT 5: breakeven stop once trade reaches +1R
            if cfg.get("use_breakeven_stop", True) and not position.get("be_moved", False):
                r_dist = position["entry_atr"] * cfg["atr_stop_mult"]
                if position["side"] == "long" and row["high"] >= position["entry"] + r_dist:
                    position["stop"] = max(position["stop"], position["entry"] * 1.001)
                    position["be_moved"] = True
                elif position["side"] == "short" and row["low"] <= position["entry"] - r_dist:
                    position["stop"] = min(position["stop"], position["entry"] * 0.999)
                    position["be_moved"] = True

            # Update peak excursion and ratchet the trailing stop
            if mode in ("trailing", "hybrid"):
                if position["side"] == "long":
                    position["peak"] = max(position["peak"], row["high"])
                    profit_atr = (position["peak"] - position["entry"]) / position["entry_atr"]
                    if profit_atr >= cfg["trail_activate_atr"]:
                        new_stop = position["peak"] - (position["entry_atr"] * cfg["trail_atr_mult"])
                        position["stop"] = max(position["stop"], new_stop)  # never loosen
                else:
                    position["peak"] = min(position["peak"], row["low"])
                    profit_atr = (position["entry"] - position["peak"]) / position["entry_atr"]
                    if profit_atr >= cfg["trail_activate_atr"]:
                        new_stop = position["peak"] + (position["entry_atr"] * cfg["trail_atr_mult"])
                        position["stop"] = min(position["stop"], new_stop)

            hit_stop = (row["low"] <= position["stop"] if position["side"] == "long"
                        else row["high"] >= position["stop"])
            # Pure trailing mode has no fixed target - the trail IS the exit
            if mode == "trailing":
                hit_tp = False
            else:
                hit_tp = (row["high"] >= position["tp"] if position["side"] == "long"
                          else row["low"] <= position["tp"])

            exit_price, reason = None, None
            if hit_stop:
                exit_price, reason = position["stop"], "stop"
            elif hit_tp:
                exit_price, reason = position["tp"], "tp"

            if exit_price:
                # Stops do NOT fill at the trigger price in fast markets.
                if reason == "stop":
                    slip_dir = -1 if position["side"] == "long" else 1
                    exit_price *= (1 + slip_dir * cfg["stop_slippage_pct"] / 100)
                direction = 1 if position["side"] == "long" else -1
                gross = (exit_price - position["entry"]) * direction * position["size"]
                fees = (position["entry"] + exit_price) * position["size"] * (fee_pct / 100)
                pnl = gross - fees
                total_fees += fees
                equity += pnl
                # A "stop" that fired above entry is really a trailing-stop profit exit
                label = reason
                if reason == "stop" and pnl > 0:
                    label = "trail_exit"
                trades.append({
                    "side": position["side"], "entry": position["entry"],
                    "exit": exit_price, "reason": label, "pnl": pnl, "equity": equity,
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

        # --- new entry ---
        # Daily loss circuit breaker (approx: 24h worth of bars)
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
                        "peak": entry, "entry_atr": row["atr"], "be_moved": False,
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
        "avg_win_pct_of_entry": round((wins["exit"]/wins["entry"]-1).mean()*100, 2) if len(wins) else 0,
        "circuit_breaker_halts": halts,
        "long_trades": int((t["side"] == "long").sum()),
        "short_trades": int((t["side"] == "short").sum()),
        "long_pnl": round(t[t["side"] == "long"]["pnl"].sum(), 2),
        "short_pnl": round(t[t["side"] == "short"]["pnl"].sum(), 2),
    }


def _tf_hours(tf: str) -> float:
    """Convert a ccxt timeframe string to hours."""
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
        # Sets the x-simulated-trading: 1 header -> OKX demo environment.
        ex.set_sandbox_mode(True)
        log.info("SANDBOX MODE ENABLED — orders route to OKX demo trading.")
    return ex


def fetch_ohlcv_mtf(ex, cfg) -> tuple:
    """Fetch both the regime timeframe (1h) and entry timeframe (15m)."""
    regime_tf = cfg.get("mtf_regime_tf", "1h")
    entry_tf = cfg.get("mtf_entry_tf", "15m")
    limit_regime = cfg.get("mtf_regime_limit", 500)
    limit_entry = cfg.get("mtf_entry_limit", 1500)

    raw_regime = ex.fetch_ohlcv(cfg["symbol"], timeframe=regime_tf, limit=limit_regime)
    raw_entry = ex.fetch_ohlcv(cfg["symbol"], timeframe=entry_tf, limit=limit_entry)

    df_regime = pd.DataFrame(raw_regime, columns=["ts", "open", "high", "low", "close", "volume"])
    df_entry = pd.DataFrame(raw_entry, columns=["ts", "open", "high", "low", "close", "volume"])
    df_regime["dt"] = pd.to_datetime(df_regime["ts"], unit="ms", utc=True)
    df_entry["dt"] = pd.to_datetime(df_entry["ts"], unit="ms", utc=True)
    return df_regime, df_entry


def timeframe_to_ms(tf: str) -> int:
    unit = tf[-1]
    n = int(tf[:-1])
    mult = {"m": 60_000, "h": 3_600_000, "d": 86_400_000}.get(unit)
    if mult is None:
        raise ValueError(f"Unsupported timeframe: {tf}")
    return n * mult


def compute_mtf_signals(df_regime: pd.DataFrame, df_entry: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Higher timeframe (1h) sets trend/regime. Lower timeframe (15m) times entry.

    CRITICAL: no lookahead. A 1h candle opening at T covers [T, T+1h) and is
    NOT closed/knowable until T+1h. We tag each 1h row with `available_at` =
    ts + its own duration, then merge_asof(direction='backward') so a 15m bar
    at time t only ever sees a 1h candle that had actually finished printing
    by time t.
    """
    regime_tf_ms = timeframe_to_ms(cfg.get("mtf_regime_tf", "1h"))

    reg = compute_signals(df_regime, cfg).copy()
    reg = reg.rename(columns={c: f"{c}_reg" for c in reg.columns if c not in ("ts", "dt")})
    reg["available_at"] = reg["ts"] + regime_tf_ms
    reg = reg.sort_values("available_at").reset_index(drop=True)

    ent = compute_signals(df_entry, cfg).copy()
    ent = ent.sort_values("ts").reset_index(drop=True)

    merged = pd.merge_asof(
        ent, reg, left_on="ts", right_on="available_at",
        direction="backward", suffixes=("", "_reg_dup"),
    )

    bull_regime = merged["bull_stack_reg"].fillna(False) & merged["regime_ok_reg"].fillna(False)
    bear_regime = merged["bear_stack_reg"].fillna(False) & merged["regime_ok_reg"].fillna(False)

    entry_long_trigger = merged["macd_cross_up"] & (merged["rsi"] > cfg["rsi_mid"])
    entry_short_trigger = merged["macd_cross_dn"] & (merged["rsi"] < cfg["rsi_mid"])

    merged["long_signal"] = bull_regime & entry_long_trigger & merged["vol_ok"]
    merged["short_signal"] = bear_regime & entry_short_trigger & merged["vol_ok"]
    if cfg.get("long_only", True):
        merged["short_signal"] = merged["short_signal"] & False

    # Stop/TP sized off the HIGHER timeframe ATR (wide enough for real trend
    # room) even though entry timing comes from the lower timeframe.
    merged["atr"] = merged["atr_reg"]
    return merged


def fetch_ohlcv(ex, cfg) -> pd.DataFrame:
    raw = ex.fetch_ohlcv(cfg["symbol"], timeframe=cfg["timeframe"], limit=cfg["candle_limit"])
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
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
        # Reconcile: warn about any pre-existing open orders
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
            # Use last CLOSED candle, not the forming one
            row = d.iloc[-2]
            bar_ts = int(row["ts"])

            if state.get("last_bar_ts") == bar_ts:
                time.sleep(cfg["poll_seconds"])
                continue
            state["last_bar_ts"] = bar_ts

            log.info(
                f"{row['dt']} close={row['close']:.2f} adx={row['adx']:.1f} "
                f"rsi={row['rsi']:.1f} atr%={row['atr_pct']:.2f} "
                f"regime_ok={bool(row['regime_ok'])} "
                f"L={bool(row['long_signal'])} S={bool(row['short_signal'])}"
            )

            # --- CIRCUIT BREAKER CHECKS ---
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
DAY_TRADING_PRESET = {
    "timeframe": "1h",
    "atr_stop_mult": 1.5,
    "atr_tp_mult": 3.0,        # 2:1 R:R, ~2-3% targets on 1h BTC
    "adx_threshold": 22,       # slightly looser: 1h trends are shorter-lived
    "require_adx_rising": False,
    "cooldown_bars": 4,
    "max_consecutive_losses": 4,
    "daily_loss_limit_pct": 4.0,
    "vol_spike_mult": 2.0,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="place real orders")
    ap.add_argument("--demo", action="store_true", help="OKX demo trading sandbox (virtual funds)")
    ap.add_argument("--allow-shorts", action="store_true", help="enable shorts (requires swap, not spot)")
    ap.add_argument("--day", action="store_true", help="day-trading preset (1h, tighter stops, more trades)")
    ap.add_argument("--exit-mode", choices=["fixed","trailing","hybrid"], help="override exit mode")
    ap.add_argument("--volume-filter", action="store_true", help="require above-average volume on entry")
    ap.add_argument("--vwap-filter", action="store_true", help="require price above/below VWAP for long/short")
    ap.add_argument("--mtf", action="store_true", help="multi-timeframe: 1h regime, 15m entry (no lookahead)")
    ap.add_argument("--minimal", action="store_true", help="only SuperTrend + VWAP, nothing else")
    ap.add_argument("--adaptive-st", action="store_true", help="volatility-adaptive SuperTrend multiplier")
    ap.add_argument("--vwap-bands", action="store_true", help="require price beyond VWAP std-dev band, not just the line")
    ap.add_argument("--signal-mode", choices=["trend","oscillator","dip","pullback","supertrend"], help="entry logic")
    ap.add_argument("--backtest", type=int, metavar="N", help="backtest last N candles")
    ap.add_argument("--timeframe", type=str, help="override timeframe (e.g. 1h, 4h, 1d)")
    ap.add_argument("--symbol", type=str, help="override symbol (e.g. BTC/USDT)")
    args = ap.parse_args()

    cfg = dict(CONFIG)
    if args.day:
        cfg.update(DAY_TRADING_PRESET)
        print("DAY-TRADING PRESET: 1h / 1.5xATR stop / 3xATR TP")
    if args.signal_mode:
        cfg["signal_mode"] = args.signal_mode
    if args.volume_filter:
        cfg["use_volume_filter"] = True
    if args.vwap_filter:
        cfg["use_vwap_filter"] = True
    if args.mtf:
        cfg["use_mtf"] = True
    if args.minimal:
        cfg["signal_mode_minimal"] = True
    if args.adaptive_st:
        cfg["use_adaptive_supertrend"] = True
    if args.vwap_bands:
        cfg["use_vwap_bands"] = True
    if args.exit_mode:
        cfg["exit_mode"] = args.exit_mode
    if args.timeframe:
        cfg["timeframe"] = args.timeframe
    if args.symbol:
        cfg["symbol"] = args.symbol
    if args.allow_shorts:
        cfg["long_only"] = False
        print("WARNING: shorts require OKX swap markets. Spot cannot short.")

    if args.live and args.demo:
        print("Choose --live OR --demo, not both.")
        return

    if args.backtest:
        ex = make_exchange(live=False)

        if cfg.get("use_mtf", False):
            df_reg, df_ent = fetch_ohlcv_mtf(ex, cfg)
            d = compute_mtf_signals(df_reg, df_ent, cfg)
            res = backtest(d, cfg)
            print(f"\n=== MTF BACKTEST: {cfg['symbol']} "
                  f"[{cfg['mtf_regime_tf']} regime -> {cfg['mtf_entry_tf']} entry] "
                  f"({len(d)} entry-candles, {d['dt'].iloc[0].date()} -> {d['dt'].iloc[-1].date()}) ===")
        else:
            cfg["candle_limit"] = min(args.backtest, 1000)
            df = fetch_ohlcv(ex, cfg)
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
