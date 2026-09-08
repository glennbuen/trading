#!/usr/bin/env python3
"""
Retest every strategy from scripts/retest_all_with_exit_rules.py with
an ADDITIONAL entry filter ANDed onto each strategy's own entry signal:
price must be "near or within striking distance of EMA(10)" —
confirmed with the user before running: % distance from close to
EMA(10) (not ATR-based), price required on the favorable side (a
pullback into value: for a long, close at or below the EMA but within
2%; the mirror for a short) — `engines/entry_filters.py`.

Same exit_rules_spec.md system as the prior retest (both variants:
flat +6% lock and ATR-trailing), same scope (14 of 20 strategies with a
real entry signal, 1d only — see scripts/retest_all_with_exit_rules.py
for why sub-daily/weekly-native strategies are excluded), same
RiskLimits() defaults, for a fair three-way comparison: original exit
-> new exit system alone -> new exit system + EMA(10) filter.

Usage: python scripts/retest_all_with_ema10_filter.py
"""

import sys

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.engines.entry_filters import compute_entry_filters, DEFAULT_EMA_PERIOD, DEFAULT_MAX_DISTANCE_PCT
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.exit_rules import ExitRulesConfig, attach_exit_indicators
from cryptobot.backtest.exit_rules_engine import run_backtest_with_exit_rules
from cryptobot.backtest.walk_forward import run_walk_forward
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from scripts.evaluate_strategy import aggregate
from scripts.retest_all_with_exit_rules import STRATEGIES, EXIT_VARIANTS


def apply_ema10_filter(signal_fn, long_col, short_col,
                        ema_period=DEFAULT_EMA_PERIOD, max_distance_pct=DEFAULT_MAX_DISTANCE_PCT):
    """Wraps an existing (signal_fn, long_col, short_col) triple to AND
    the near-EMA(N)-pullback filter onto its entry columns."""
    def filtered_signal_fn(df, exit_cfg, _fn=signal_fn, _long=long_col, _short=short_col,
                            _period=ema_period, _pct=max_distance_pct):
        d = _fn(df, exit_cfg=exit_cfg)
        d = compute_entry_filters(d, ema_period=_period, max_distance_pct=_pct)
        d["long_signal_ema10"] = d[_long].fillna(False) & d["ef_near_ema_long"]
        d["short_signal_ema10"] = (d[_short].fillna(False) & d["ef_near_ema_short"]) if _short else False
        return d
    return filtered_signal_fn, "long_signal_ema10", ("short_signal_ema10" if short_col else None)


def run_one(md, symbol, signal_fn, long_col, short_col, exit_cfg):
    df = md.get_ohlcv(symbol, "1d", 3000)

    def wrapped(d, _fn=signal_fn, _cfg=exit_cfg):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(df, wrapped, long_col, short_col, RiskLimits(), exit_cfg,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows)


def run_spyfrat(md, symbol, exit_cfg):
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)

    def base_signal_fn(d, exit_cfg, _pre=pre_merged):
        d2 = compute_volatility(d.copy())
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        d2 = attach_exit_indicators(d2, exit_cfg)
        return d2

    filtered_fn, long_col, short_col = apply_ema10_filter(base_signal_fn, "long_signal", None)

    def wrapped(d, _fn=filtered_fn, _cfg=exit_cfg):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(pre_merged, wrapped, long_col, short_col, RiskLimits(), exit_cfg,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    symbols = ["BTC/USDT", "ETH/USDT"]

    print("\n" + "=" * 100)
    print("EXIT RULES + EMA(10)-PULLBACK FILTER RETEST — 1d, both exit variants")
    print("=" * 100)

    for name, (signal_fn, long_col, short_col) in STRATEGIES.items():
        filtered_fn, f_long, f_short = apply_ema10_filter(signal_fn, long_col, short_col)
        for symbol in symbols:
            for variant_name, cfg in EXIT_VARIANTS.items():
                try:
                    agg = run_one(md, symbol, filtered_fn, f_long, f_short, cfg)
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
                agg = run_spyfrat(md, symbol, cfg)
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
