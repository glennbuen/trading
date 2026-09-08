#!/usr/bin/env python3
"""
Day-Trading Retest — all 14 strategies with a real entry signal, redone
per the user's own design: 1h + 15m for trend (both must agree — see
daytrading/engines/trend_filter.py), 5m for entry. Each strategy's own
distinctive entry-trigger logic is reused UNCHANGED, recomputed on 5m
OHLCV, gated by the new trend filter instead of whatever daily/weekly
context the original strategy used.

Exit mechanism: plain ATR stop + fixed 2R target (StopTargetConfig's
"atr" method — this project's original baseline evaluation default,
scripts/evaluate_strategy.py) rather than either the exit_rules_spec.md
system or each strategy's own bespoke exit — this retest is
specifically about the ENTRY timeframe redesign, not a second exit-
system experiment layered on top of it. Flagged explicitly.

COST MODEL — corrected, and why: BacktestCosts' project-wide default
(stop_slippage_pct=0.4%) was calibrated for daily-swing trading, where a
typical ATR-based stop sits several percent from entry, so 0.4%
slippage is a modest fraction of that distance. On 5m bars, a 1.5xATR
stop on BTC/ETH is typically under 0.2% of price — smaller than the
0.4% slippage assumption ALONE, which would mechanically force every
stop-loss exit to realize MORE than the entire 1R risk distance in
slippage before the trade's own P&L is even considered, regardless of
whether the entry signal has any real edge. Caught via diagnostic
comparison (a raw, unfiltered TITA run showed the same catastrophic PF
as the trend-filtered version — ruling out the trend filter as the
cause — before this cost-model mismatch was found and fixed) rather
than accepted at face value. Corrected here to a slippage assumption
realistic for BTC/USDT and ETH/USDT spot execution on OKX (deep, tight-
spread markets) regardless of holding period: 0.05% for both entry and
stop fills, matching this project's existing entry_slippage_pct default
rather than the daily-calibrated stop_slippage_pct.

BTC/USDT and ETH/USDT, 5m entry data fetched once per symbol and shared
across all 14 strategies (the 1h/15m/5m datasets are identical
regardless of which strategy is being evaluated). 14-day walk-forward
windows, matching the only other 5m-timeframe strategy tested in this
project (4-Hour Range Scalp).

Usage: python scripts/evaluate_daytrading_all.py
"""

import sys

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig, BacktestCosts, run_backtest
from cryptobot.backtest.walk_forward import run_walk_forward
from daytrading.strategies.wrapper import build_daytrading_signal_fn
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

STRATEGIES = {
    "Breakout+Retest (B)": (compute_breakout_retest, "br_long_entry_signal", "br_short_entry_signal"),
    "Breakout (A)": (compute_breakout, "long_signal", "short_signal"),
    "Trend Pullback (C)": (compute_trend_pullback, "tp_long_entry_signal", "tp_short_entry_signal"),
    "Liquidity Sweep Reversal (D)": (compute_liquidity_sweep_reversal, "long_signal", "short_signal"),
    "Ichimoku Cross": (compute_ichimoku_cross, "long_signal", "short_signal"),
    "MFI Reversal": (compute_mfi_reversal, "long_signal", "short_signal"),
    "MAMA": (compute_mama, "long_signal", None),
    "BOPIS": (compute_bopis, "long_signal", None),
    "PAPA": (compute_papa, "long_signal", None),
    "TITA": (compute_tita, "long_signal", None),
    "20% Support Bounce": (compute_support_20pct, "long_signal", None),
    "SWAG": (compute_swag, "long_signal", None),
    "3-Step Formula": (compute_three_step_formula, "long_signal", "short_signal"),
}


def spyfrat_compute(df):
    d = df.copy()
    d["long_signal"] = bollinger_breakout_up(d, 50, 0.20)
    return d


STOP_TARGET = StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0)
# Realistic for liquid BTC/USDT & ETH/USDT spot execution, NOT the
# daily-calibrated 0.4% stop_slippage_pct default — see module docstring.
INTRADAY_COSTS = BacktestCosts(taker_fee_pct=0.10, entry_slippage_pct=0.05, stop_slippage_pct=0.05)
WINDOW_DAYS = 14


def run_one(entry_df, tf1_df, tf2_df, compute_fn, long_col, short_col):
    signal_fn = build_daytrading_signal_fn(compute_fn, long_col, short_col, tf1_df, tf2_df)
    windows = run_walk_forward(entry_df, signal_fn, "long_signal_dt", "short_signal_dt",
                                RiskLimits(), STOP_TARGET, window_days=WINDOW_DAYS, step_days=WINDOW_DAYS,
                                costs=INTRADAY_COSTS)
    return aggregate(windows)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    print("\n" + "=" * 100)
    print("DAY-TRADING RETEST — 1h+15m trend (both agree), 5m entry, ATR/2R exit")
    print("=" * 100)

    for symbol in ["BTC/USDT", "ETH/USDT"]:
        print(f"\nFetching {symbol} 5m/15m/1h data...", file=sys.stderr)
        entry_df = md.get_ohlcv(symbol, "5m", 50000)
        tf2_df = md.get_ohlcv(symbol, "15m", 17000)
        tf1_df = md.get_ohlcv(symbol, "1h", 4500)
        print(f"  5m: {len(entry_df)} candles ({entry_df['dt'].iloc[0].date()} -> {entry_df['dt'].iloc[-1].date()})"
              f"  15m: {len(tf2_df)}  1h: {len(tf1_df)}", file=sys.stderr)

        for name, (compute_fn, long_col, short_col) in STRATEGIES.items():
            try:
                agg = run_one(entry_df, tf1_df, tf2_df, compute_fn, long_col, short_col)
            except Exception as e:
                print(f"  ERROR {name} {symbol}: {e}", file=sys.stderr)
                continue
            print(f"{name:30s} {symbol:10s} trades={agg.get('total_trades', 0):>4} "
                  f"PF={agg.get('profit_factor', float('nan')):>7} "
                  f"win%={agg.get('win_rate_pct', 0):>6} "
                  f"avgR={agg.get('avg_r_multiple', float('nan')):>7} "
                  f"windows={agg.get('windows_profitable', 0)}/{agg.get('windows_total', 0)} "
                  f"chainDD%={agg.get('chained_max_drawdown_pct', 0):>6}")

        try:
            agg = run_one(entry_df, tf1_df, tf2_df, spyfrat_compute, "long_signal", None)
            print(f"{'SPYFRAT Core System':30s} {symbol:10s} trades={agg.get('total_trades', 0):>4} "
                  f"PF={agg.get('profit_factor', float('nan')):>7} "
                  f"win%={agg.get('win_rate_pct', 0):>6} "
                  f"avgR={agg.get('avg_r_multiple', float('nan')):>7} "
                  f"windows={agg.get('windows_profitable', 0)}/{agg.get('windows_total', 0)} "
                  f"chainDD%={agg.get('chained_max_drawdown_pct', 0):>6}")
        except Exception as e:
            print(f"  ERROR SPYFRAT {symbol}: {e}", file=sys.stderr)

    print("\nDONE.")


if __name__ == "__main__":
    main()
