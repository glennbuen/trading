#!/usr/bin/env python3
"""
3-Step Formula — walk-forward evaluation harness, same pattern as
scripts/evaluate_swag.py. No parameters tuned based on output. Both
sides evaluated (long via demand zones, short via supply zones), since
the video explicitly demonstrates both and this project's backtest
engine supports shorts.

Usage: python scripts/evaluate_three_step_formula.py
"""

import sys

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward
from cryptobot.strategies.three_step_formula import compute_three_step_formula, DEFAULT_MIN_RR
from scripts.evaluate_strategy import aggregate


def signal_fn(df: pd.DataFrame) -> pd.DataFrame:
    d = compute_volatility(df.copy())
    return compute_three_step_formula(d)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    configs = [
        ("BTC/USDT", "1h", 8000, 45),
        ("ETH/USDT", "1h", 8000, 45),
        ("BTC/USDT", "1d", 3000, 180),
        ("ETH/USDT", "1d", 3000, 180),
    ]

    stop_target = StopTargetConfig(method="structure", structure_stop_col="tsf_structure_stop",
                                    structure_target_col="tsf_structure_target", min_rr=DEFAULT_MIN_RR,
                                    atr_mult_stop=1.5)

    print("\n" + "=" * 78)
    print(f"3-STEP FORMULA — WALK-FORWARD EVALUATION (min_rr={DEFAULT_MIN_RR})")
    print("=" * 78)

    for symbol, tf, candles, window_days in configs:
        df = md.get_ohlcv(symbol, tf, candles)
        windows = run_walk_forward(df, signal_fn, "long_signal", "short_signal", RiskLimits(), stop_target,
                                    window_days=window_days, step_days=window_days)
        agg = aggregate(windows)
        print(f"\n--- {symbol} {tf} ({len(df)} candles, "
              f"{df['dt'].iloc[0].date()} -> {df['dt'].iloc[-1].date()}) ---")
        if agg["total_trades"] == 0:
            print("  NO TRADES across any window.")
            continue
        print(f"  trades={agg['total_trades']} win%={agg['win_rate_pct']} PF={agg['profit_factor']} "
              f"avgR={agg['avg_r_multiple']} windows={agg['windows_profitable']}/{agg['windows_total']} "
              f"chainedDD%={agg['chained_max_drawdown_pct']}")
        print("  per-window:")
        for w in windows:
            r = w.result
            print(f"    {w.label}: {r.num_trades} trades, PF={r.profit_factor}, "
                  f"win%={r.win_rate_pct}, net%={r.net_return_pct}")


if __name__ == "__main__":
    main()
