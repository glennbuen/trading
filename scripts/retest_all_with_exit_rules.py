#!/usr/bin/env python3
"""
Retest every strategy with a real entry signal against
exit_rules_spec.md's new position-management system (ratcheted stop,
time stop, partial profit-take, EMA(8)/EMA(4) de-risk), replacing each
strategy's ORIGINAL exit mechanism entirely — only entry logic is
reused. Runs both confirmed exit-rules variants (flat +6% lock vs the
ATR-trailing ADDITION) and reports both, on BTC/USDT + ETH/USDT, 1d
only (see docs/EVALUATION_EXIT_RULES_RETEST.md for why: the spec is
explicitly scoped to "Daily Timeframe Swing/Position Trades" - EMA(8)/
EMA(4) on daily closes, a 5-8 DAY time stop - which doesn't translate
to sub-daily or weekly-native strategies).

Excluded, and why:
  - Bebemon, Ceiling/Follow-Through: zero real-data entry signals on
    either symbol - a different exit system cannot create trades where
    there are no entries.
  - FISHBALL (30m), Day Trading ALMA (15m), 4-Hour Range Scalp (5m):
    intraday/scalping strategies, not daily swing trades - a 5-8 DAY
    time stop and daily-close EMA rules don't apply to their own native
    timeframe.
  - CALMA (1w): weekly-native, same reasoning.

No parameter tuned in response to any result — every run below uses
exit_rules.py's own defaults (or the ATR-trailing toggle, itself
user-confirmed before implementation) applied uniformly across every
strategy.
"""

import sys

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.exit_rules import ExitRulesConfig, attach_exit_indicators
from cryptobot.backtest.exit_rules_engine import run_backtest_with_exit_rules
from cryptobot.backtest.walk_forward import run_walk_forward
from scripts.evaluate_strategy import aggregate

from cryptobot.strategies.breakout_retest import compute_breakout_retest
from cryptobot.strategies.breakout import compute_breakout
from cryptobot.strategies.trend_pullback import compute_trend_pullback
from cryptobot.strategies.liquidity_sweep_reversal import compute_liquidity_sweep_reversal
from cryptobot.strategies.ichimoku_cross import compute_ichimoku_cross
from cryptobot.strategies.mfi_reversal import compute_mfi_reversal
from cryptobot.strategies.mama import compute_mama
from cryptobot.strategies.bopis import compute_bopis
from cryptobot.strategies.papa import compute_papa
from cryptobot.strategies.tita import compute_tita
from cryptobot.strategies.support_20pct import compute_support_20pct
from cryptobot.strategies.swag import compute_swag
from cryptobot.strategies.three_step_formula import compute_three_step_formula
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from cryptobot.engines.moving_averages import bollinger_bands


def wrap(compute_fn, long_col, short_col=None, **kwargs):
    """Builds a signal_fn: compute_volatility -> strategy's own entry
    logic -> attach_exit_indicators, matching the shared shape every
    non-SPYFRAT strategy below needs."""
    def signal_fn(df, exit_cfg=ExitRulesConfig()):
        d = compute_volatility(df.copy())
        d = compute_fn(d, **kwargs)
        d = attach_exit_indicators(d, exit_cfg)
        return d
    return signal_fn, long_col, short_col


STRATEGIES = {
    "Breakout+Retest (B)": wrap(compute_breakout_retest, "br_long_entry_signal", "br_short_entry_signal"),
    "Breakout (A)": wrap(compute_breakout, "long_signal", "short_signal"),
    "Trend Pullback (C)": wrap(compute_trend_pullback, "tp_long_entry_signal", "tp_short_entry_signal"),
    "Liquidity Sweep Reversal (D)": wrap(compute_liquidity_sweep_reversal, "long_signal", "short_signal"),
    "Ichimoku Cross": wrap(compute_ichimoku_cross, "long_signal", "short_signal"),
    "MFI Reversal": wrap(compute_mfi_reversal, "long_signal", "short_signal"),
    "MAMA": wrap(compute_mama, "long_signal", None),
    "BOPIS": wrap(compute_bopis, "long_signal", None),
    "PAPA": wrap(compute_papa, "long_signal", None),
    "TITA": wrap(compute_tita, "long_signal", None),
    "20% Support Bounce": wrap(compute_support_20pct, "long_signal", None),
    "SWAG": wrap(compute_swag, "long_signal", None),
    "3-Step Formula": wrap(compute_three_step_formula, "long_signal", "short_signal"),
}

EXIT_VARIANTS = {
    "flat_lock": ExitRulesConfig(enable_atr_trailing_above_lock=False),
    "atr_trailing": ExitRulesConfig(enable_atr_trailing_above_lock=True),
}


def run_one(md, symbol, signal_fn, long_col, short_col, exit_cfg):
    df = md.get_ohlcv(symbol, "1d", 3000)

    def wrapped(d, _fn=signal_fn, _cfg=exit_cfg):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(df, wrapped, long_col, short_col, RiskLimits(),
                                exit_cfg, window_days=180, step_days=180,
                                backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows), len(df)


def run_spyfrat(md, symbol, exit_cfg):
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)

    def signal_fn(d, _pre=pre_merged, _cfg=exit_cfg):
        d2 = compute_volatility(d.copy())
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        d2 = attach_exit_indicators(d2, _cfg)
        return d2

    windows = run_walk_forward(pre_merged, signal_fn, "long_signal", None, RiskLimits(),
                                exit_cfg, window_days=180, step_days=180,
                                backtest_fn=run_backtest_with_exit_rules)
    return aggregate(windows), len(daily)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    symbols = ["BTC/USDT", "ETH/USDT"]

    print("\n" + "=" * 100)
    print("EXIT RULES RETEST — every strategy with a real entry signal, 1d, both exit variants")
    print("=" * 100)

    rows = []
    for name, (signal_fn, long_col, short_col) in STRATEGIES.items():
        for symbol in symbols:
            for variant_name, cfg in EXIT_VARIANTS.items():
                try:
                    agg, n = run_one(md, symbol, signal_fn, long_col, short_col, cfg)
                except Exception as e:
                    print(f"  ERROR {name} {symbol} {variant_name}: {e}", file=sys.stderr)
                    continue
                rows.append((name, symbol, variant_name, agg))
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
                agg, n = run_spyfrat(md, symbol, cfg)
            except Exception as e:
                print(f"  ERROR SPYFRAT {symbol} {variant_name}: {e}", file=sys.stderr)
                continue
            rows.append(("SPYFRAT Core System", symbol, variant_name, agg))
            print(f"{'SPYFRAT Core System':30s} {symbol:10s} {variant_name:13s} "
                  f"trades={agg.get('total_trades', 0):>4} "
                  f"PF={agg.get('profit_factor', float('nan')):>7} "
                  f"win%={agg.get('win_rate_pct', 0):>6} "
                  f"avgR={agg.get('avg_r_multiple', float('nan')):>7} "
                  f"chainDD%={agg.get('chained_max_drawdown_pct', 0):>6}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
