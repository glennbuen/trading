#!/usr/bin/env python3
"""
Parameter sensitivity sweep (architecture spec §26): perturb each key
parameter ±10%/±20% around its default, one at a time, and check whether
the result collapses or stays broadly similar. Per spec: "If changing a
parameter from 1.5 to 1.53 dramatically changes results, flag it as
potentially overfit." This closes the one explicitly-flagged gap in
Phase 6's evaluation of Breakout+Retest (docs/EVALUATION_BREAKOUT_RETEST.md).

Run on BTC/USDT 1h only (the config with the most trades, hence the most
statistical power to detect a real sensitivity effect) — not exhaustive
across all four Phase 6 configs, which would multiply runtime for
marginal extra insight into the same underlying question.

Usage:
    python scripts/parameter_sensitivity.py
"""

import sys
from dataclasses import dataclass, replace

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct

SYMBOL, TIMEFRAME, CANDLES, WINDOW_DAYS = "BTC/USDT", "1h", 8000, 45

BASELINE = {
    "atr_mult_stop": 1.5,
    "target_r_multiple": 2.0,
    "volume_threshold": 1.2,
    "retest_window": 10,
}
PERTURBATIONS_PCT = [-20, -10, 0, 10, 20]


def make_signal_fn(volume_threshold: float, retest_window: int):
    def signal_fn(df: pd.DataFrame) -> pd.DataFrame:
        from cryptobot.strategies.breakout_retest import compute_breakout_retest
        d = compute_volatility(df.copy())
        d = compute_breakout_retest(d, volume_threshold=volume_threshold, retest_window=retest_window)
        return d
    return signal_fn


def aggregate(windows) -> dict:
    all_trades = [t for w in windows for t in w.result.trades]
    if not all_trades:
        return {"total_trades": 0, "profit_factor": float("nan"), "win_rate_pct": 0.0,
                "avg_r_multiple": float("nan"), "chained_max_dd_pct": 0.0}
    wins = [t for t in all_trades if t.pnl > 0]
    losses = [t for t in all_trades if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    return {
        "total_trades": len(all_trades),
        "win_rate_pct": round(len(wins) / len(all_trades) * 100, 2),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_r_multiple": round(sum(t.r_multiple for t in all_trades) / len(all_trades), 3),
        "chained_max_dd_pct": round(chained_max_drawdown_pct(windows), 2),
    }


def run_variant(df: pd.DataFrame, param: str, value: float) -> dict:
    params = dict(BASELINE)
    params[param] = value

    signal_fn = make_signal_fn(params["volume_threshold"], params["retest_window"])
    stop_target = StopTargetConfig(method="atr", atr_mult_stop=params["atr_mult_stop"],
                                    target_r_multiple=params["target_r_multiple"])
    windows = run_walk_forward(
        df, signal_fn, "br_long_entry_signal", "br_short_entry_signal",
        RiskLimits(), stop_target, window_days=WINDOW_DAYS, step_days=WINDOW_DAYS,
    )
    return aggregate(windows)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    print(f"Fetching {SYMBOL} {TIMEFRAME} ({CANDLES} candles)...", file=sys.stderr)
    df = md.get_ohlcv(SYMBOL, TIMEFRAME, CANDLES)
    print(f"{len(df)} candles, {df['dt'].iloc[0]} -> {df['dt'].iloc[-1]}\n")

    print("=" * 90)
    print(f"PARAMETER SENSITIVITY — Breakout+Retest on {SYMBOL} {TIMEFRAME} (spec §26)")
    print("=" * 90)

    for param, baseline_value in BASELINE.items():
        print(f"\n--- {param} (baseline={baseline_value}) ---")
        print(f"  {'change':>8} {'value':>8} {'trades':>7} {'win%':>7} {'PF':>7} {'avgR':>8} {'chainDD%':>9}")
        for pct in PERTURBATIONS_PCT:
            value = baseline_value * (1 + pct / 100)
            if param == "retest_window":
                value = max(1, round(value))
            agg = run_variant(df, param, value)
            label = "baseline" if pct == 0 else f"{pct:+d}%"
            print(f"  {label:>8} {value:>8.3f} {agg['total_trades']:>7} "
                  f"{agg['win_rate_pct']:>7.2f} {agg['profit_factor']:>7} "
                  f"{agg['avg_r_multiple']:>8} {agg['chained_max_dd_pct']:>9}")


if __name__ == "__main__":
    main()
