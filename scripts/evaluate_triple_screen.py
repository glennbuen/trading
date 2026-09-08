#!/usr/bin/env python3
"""
Triple Screen (Alexander Elder) — walk-forward evaluation harness, same
pattern as scripts/evaluate_strategy.py. No parameters tuned based on
output. Weekly + daily, per the system's own design (Screen 1 on the
higher timeframe, Screens 2-3 on the trading timeframe) — BTC/USDT and
ETH/USDT only (this project's OKX data pipeline).

Usage: python scripts/evaluate_triple_screen.py
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
from cryptobot.strategies.triple_screen import compute_triple_screen
from scripts.evaluate_strategy import aggregate


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    stop_target = StopTargetConfig(method="structure", structure_stop_col="ts_structure_stop",
                                    atr_mult_stop=1.5, target_r_multiple=2.0)

    print("\n" + "=" * 78)
    print("TRIPLE SCREEN (Elder) — WALK-FORWARD EVALUATION (weekly + 1d)")
    print("=" * 78)

    for symbol in ["BTC/USDT", "ETH/USDT"]:
        daily = md.get_ohlcv(symbol, "1d", 3000)
        weekly = md.get_ohlcv(symbol, "1w", 500)

        def signal_fn(d, _weekly=weekly):
            d2 = compute_volatility(d.copy())
            return compute_triple_screen(d2, _weekly)

        windows = run_walk_forward(daily, signal_fn, "long_signal", "short_signal", RiskLimits(), stop_target,
                                    window_days=180, step_days=180)
        agg = aggregate(windows)
        print(f"\n--- {symbol} ({len(daily)} candles, "
              f"{daily['dt'].iloc[0].date()} -> {daily['dt'].iloc[-1].date()}) ---")
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
