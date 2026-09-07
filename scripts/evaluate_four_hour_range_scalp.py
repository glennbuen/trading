#!/usr/bin/env python3
"""
4-Hour Range Scalp — walk-forward evaluation harness, same pattern as
scripts/evaluate_swag.py. No parameters tuned based on output. 5-minute
timeframe only, matching the video's own stated setup; short (14-day)
walk-forward windows since a scalping strategy accumulates trades much
faster than the daily/hourly strategies elsewhere in this project.

Usage: python scripts/evaluate_four_hour_range_scalp.py
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
from cryptobot.strategies.four_hour_range_scalp import compute_four_hour_range_scalp
from scripts.evaluate_strategy import aggregate


def signal_fn(df: pd.DataFrame) -> pd.DataFrame:
    d = compute_volatility(df.copy())
    return compute_four_hour_range_scalp(d)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    configs = [
        ("BTC/USDT", "5m", 50000, 14),
        ("ETH/USDT", "5m", 50000, 14),
    ]

    stop_target = StopTargetConfig(method="structure", structure_stop_col="fhr_structure_stop",
                                    target_r_multiple=2.0, atr_mult_stop=1.5)

    print("\n" + "=" * 78)
    print("4-HOUR RANGE SCALP — WALK-FORWARD EVALUATION (5m, target=2R)")
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
        print("  per-window (first 20 shown):")
        for w in windows[:20]:
            r = w.result
            print(f"    {w.label}: {r.num_trades} trades, PF={r.profit_factor}, "
                  f"win%={r.win_rate_pct}, net%={r.net_return_pct}")


if __name__ == "__main__":
    main()
