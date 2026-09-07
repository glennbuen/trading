#!/usr/bin/env python3
"""
Strategy evaluation harness — runs a strategy through walk-forward across
symbols/timeframes and prints an honest report per architecture spec §39
("Final Strategy Evaluation"). Built generically (strategy passed in as a
signal_fn + column names) so it's reusable for the other 3 strategies in
Phase 11's comparison, not a one-off script for Breakout+Retest alone.

Usage:
    python scripts/evaluate_strategy.py

No parameters are tuned based on what comes out of a run — every config
here is the strategy/engine defaults, run once, reported as-is. That is
the entire point of this script existing separately from ad hoc
exploration.
"""

import sys
from dataclasses import dataclass

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, WalkForwardWindow


@dataclass
class EvalRun:
    symbol: str
    timeframe: str
    candles: int
    window_days: int


def aggregate(windows: list[WalkForwardWindow]) -> dict:
    all_trades = [t for w in windows for t in w.result.trades]
    if not all_trades:
        return {"total_trades": 0}

    wins = [t for t in all_trades if t.pnl > 0]
    losses = [t for t in all_trades if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))

    profitable_windows = sum(1 for w in windows if w.result.num_trades > 0 and w.result.net_return_pct > 0)
    traded_windows = sum(1 for w in windows if w.result.num_trades > 0)

    worst_losing_streak = max((w.result.max_consecutive_losses for w in windows), default=0)
    worst_drawdown = max((w.result.max_drawdown_pct for w in windows), default=0.0)

    return {
        "total_trades": len(all_trades),
        "win_rate_pct": round(len(wins) / len(all_trades) * 100, 2),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_r_multiple": round(sum(t.r_multiple for t in all_trades) / len(all_trades), 3),
        "total_fees": round(sum(t.fees for t in all_trades), 2),
        "windows_total": len(windows),
        "windows_traded": traded_windows,
        "windows_profitable": profitable_windows,
        "worst_losing_streak": worst_losing_streak,
        "worst_window_drawdown_pct": round(worst_drawdown, 2),
    }


def signal_fn(df: pd.DataFrame) -> pd.DataFrame:
    from cryptobot.strategies.breakout_retest import compute_breakout_retest
    d = compute_volatility(df.copy())
    d = compute_breakout_retest(d)
    return d


def run_one(ex, md, run: EvalRun) -> dict:
    df = md.get_ohlcv(run.symbol, run.timeframe, run.candles)
    actual_candles = len(df)
    windows = run_walk_forward(
        df, signal_fn, "br_long_entry_signal", "br_short_entry_signal",
        RiskLimits(), StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0),
        window_days=run.window_days, step_days=run.window_days,
    )
    agg = aggregate(windows)
    agg.update({
        "symbol": run.symbol, "timeframe": run.timeframe,
        "candles_requested": run.candles, "candles_actual": actual_candles,
        "date_range": f"{df['dt'].iloc[0].date()} -> {df['dt'].iloc[-1].date()}",
    })
    return agg, windows


def print_report(results: list[tuple[dict, list]]):
    print("\n" + "=" * 78)
    print("BREAKOUT + RETEST — WALK-FORWARD EVALUATION (spec §39)")
    print("=" * 78)

    for agg, windows in results:
        print(f"\n--- {agg['symbol']} {agg['timeframe']} "
              f"({agg['candles_actual']}/{agg['candles_requested']} candles requested, "
              f"{agg['date_range']}) ---")
        if agg["total_trades"] == 0:
            print("  NO TRADES across any window.")
            continue
        print(f"  windows: {agg['windows_total']} total, {agg['windows_traded']} traded, "
              f"{agg['windows_profitable']} net profitable")
        print(f"  total_trades:        {agg['total_trades']}")
        print(f"  win_rate_pct:        {agg['win_rate_pct']}")
        print(f"  profit_factor:       {agg['profit_factor']}")
        print(f"  avg_r_multiple:      {agg['avg_r_multiple']}")
        print(f"  total_fees:          {agg['total_fees']}")
        print(f"  worst_losing_streak: {agg['worst_losing_streak']}")
        print(f"  worst_window_dd_pct: {agg['worst_window_drawdown_pct']}")
        print("  per-window breakdown:")
        for w in windows:
            r = w.result
            print(f"    {w.label}: {r.num_trades} trades, PF={r.profit_factor}, "
                  f"win%={r.win_rate_pct}, net%={r.net_return_pct}, maxDD%={r.max_drawdown_pct}")


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    runs = [
        EvalRun("BTC/USDT", "1h", 8000, 45),
        EvalRun("ETH/USDT", "1h", 8000, 45),
        EvalRun("BTC/USDT", "1d", 3000, 180),
        EvalRun("ETH/USDT", "1d", 3000, 180),
    ]

    results = []
    for run in runs:
        print(f"Fetching {run.symbol} {run.timeframe} ({run.candles} candles)...", file=sys.stderr)
        agg, windows = run_one(ex, md, run)
        results.append((agg, windows))

    print_report(results)


if __name__ == "__main__":
    main()
