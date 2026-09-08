#!/usr/bin/env python3
"""
Retest every strategy from scripts/retest_all_with_exit_rules.py with
the CORRECTED entry composition: "entry is after breakout, buy at the
pullback around EMA(10)" (the user's own phrasing, after the first,
same-bar version was found to crush breakout-style entries to zero
trades — see docs/EVALUATION_EMA10_FILTER_RETEST.md).

Each strategy's own original entry signal is now an ARMING event (a
breakout occurred), not the entry itself. The actual entry fires on the
FIRST bar, within a 10-bar window after that breakout, where price has
pulled back near EMA(10) on the favorable side (2% distance, matching
the already-confirmed definition) — `engines.entry_filters.
pullback_entry_after_breakout`.

Same exit_rules_spec.md system as both prior retests (both variants),
same scope (14 of 20 strategies with a real entry signal, 1d only),
same RiskLimits() defaults.

Usage: python scripts/retest_all_pullback_after_breakout.py
"""

import sys

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.engines.entry_filters import (
    compute_entry_filters, pullback_entry_after_breakout,
    DEFAULT_EMA_PERIOD, DEFAULT_MAX_DISTANCE_PCT, DEFAULT_ARMING_WINDOW,
)
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.exit_rules import ExitRulesConfig, attach_exit_indicators
from cryptobot.backtest.exit_rules_engine import run_backtest_with_exit_rules
from cryptobot.backtest.walk_forward import run_walk_forward
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from scripts.evaluate_strategy import aggregate
from scripts.retest_all_with_exit_rules import STRATEGIES, EXIT_VARIANTS


def apply_pullback_after_breakout(signal_fn, long_col, short_col,
                                   ema_period=DEFAULT_EMA_PERIOD, max_distance_pct=DEFAULT_MAX_DISTANCE_PCT,
                                   arming_window=DEFAULT_ARMING_WINDOW):
    """Wraps an existing (signal_fn, long_col, short_col) triple: the
    original entry columns become arming events, the actual entry fires
    on the first EMA(10) pullback touch within `arming_window` bars
    after each one."""
    def wrapped_signal_fn(df, exit_cfg, _fn=signal_fn, _long=long_col, _short=short_col,
                           _period=ema_period, _pct=max_distance_pct, _window=arming_window):
        d = _fn(df, exit_cfg=exit_cfg)
        d = compute_entry_filters(d, ema_period=_period, max_distance_pct=_pct)
        breakout_long = d[_long].fillna(False)
        d["long_signal_pullback"] = pullback_entry_after_breakout(breakout_long, d["ef_near_ema_long"], _window)
        if _short:
            breakout_short = d[_short].fillna(False)
            d["short_signal_pullback"] = pullback_entry_after_breakout(breakout_short, d["ef_near_ema_short"], _window)
        else:
            d["short_signal_pullback"] = False
        return d
    return wrapped_signal_fn, "long_signal_pullback", ("short_signal_pullback" if short_col else None)


def run_one(md, symbol, signal_fn, long_col, short_col, exit_cfg):
    df = md.get_ohlcv(symbol, "1d", 3000)

    def wrapped(d, _fn=signal_fn, _cfg=exit_cfg):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(df, wrapped, long_col, short_col, RiskLimits(), exit_cfg,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows), windows


def run_spyfrat(md, symbol, exit_cfg):
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)

    def base_signal_fn(d, exit_cfg, _pre=pre_merged):
        d2 = compute_volatility(d.copy())
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        d2 = attach_exit_indicators(d2, exit_cfg)
        return d2

    wrapped_fn, long_col, short_col = apply_pullback_after_breakout(base_signal_fn, "long_signal", None)

    def wrapped(d, _fn=wrapped_fn, _cfg=exit_cfg):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(pre_merged, wrapped, long_col, short_col, RiskLimits(), exit_cfg,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows), windows


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    symbols = ["BTC/USDT", "ETH/USDT"]

    print("\n" + "=" * 100)
    print("BREAKOUT -> PULLBACK-TO-EMA(10) ENTRY RETEST — 1d, both exit variants")
    print("=" * 100)

    for name, (signal_fn, long_col, short_col) in STRATEGIES.items():
        wrapped_fn, w_long, w_short = apply_pullback_after_breakout(signal_fn, long_col, short_col)
        for symbol in symbols:
            for variant_name, cfg in EXIT_VARIANTS.items():
                try:
                    agg, _ = run_one(md, symbol, wrapped_fn, w_long, w_short, cfg)
                except Exception as e:
                    print(f"  ERROR {name} {symbol} {variant_name}: {e}", file=sys.stderr)
                    continue
                print(f"{name:30s} {symbol:10s} {variant_name:13s} "
                      f"trades={agg.get('total_trades', 0):>4} "
                      f"PF={agg.get('profit_factor', float('nan')):>7} "
                      f"win%={agg.get('win_rate_pct', 0):>6} "
                      f"avgR={agg.get('avg_r_multiple', float('nan')):>7} "
                      f"chainDD%={agg.get('chained_max_drawdown_pct', 0):>6}")

    print("\n" + "=" * 100)
    print("SPYFRAT CORE SYSTEM (multi-timeframe, handled separately)")
    print("=" * 100)
    for symbol in symbols:
        for variant_name, cfg in EXIT_VARIANTS.items():
            try:
                agg, _ = run_spyfrat(md, symbol, cfg)
            except Exception as e:
                print(f"  ERROR SPYFRAT {symbol} {variant_name}: {e}", file=sys.stderr)
                continue
            print(f"{'SPYFRAT Core System':30s} {symbol:10s} {variant_name:13s} "
                  f"trades={agg.get('total_trades', 0):>4} "
                  f"PF={agg.get('profit_factor', float('nan')):>7} "
                  f"win%={agg.get('win_rate_pct', 0):>6} "
                  f"avgR={agg.get('avg_r_multiple', float('nan')):>7} "
                  f"chainDD%={agg.get('chained_max_drawdown_pct', 0):>6}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
