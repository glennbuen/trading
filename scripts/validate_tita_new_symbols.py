#!/usr/bin/env python3
"""
TITA — sensitivity sweep + holdout validation for the top-20 screen's
three strongest names (XLM, DOGE, SOL — see docs/TITA_TOP20_SCREEN.md).

Same two checks TITA itself had to pass before being trusted enough for
paper trading on BTC/ETH:
  1. Parameter sensitivity sweep (scripts/parameter_sensitivity_tita.py's
     method) — perturb alma_window/rsi_length/rsi_lower/rsi_upper by
     -20/-10/0/+10/+20% each, one at a time. A real edge shouldn't
     collapse from a small nudge to any one parameter ("no cliffs");
     a result that only exists at the exact baseline values is much more
     likely overfitting than a genuine edge.
  2. Holdout validation (scripts/holdout_validation_tita.py's method) —
     compute the signal ONCE on full history (correct warmup), split
     chronologically at (latest - 365 days), backtest the holdout slice
     on its own, plus a per-quarter breakdown to catch thin-sample
     artifacts within the holdout itself.

Same honesty note as both source scripts: this is still not genuine
prospective validation — that's what paper trading itself provides. This
script is the precondition check before any of these three names would
even be considered for that stage, exactly the bar BTC/ETH had to clear.
Nothing tuned, same TITA defaults, same stop/risk config throughout.
"""

import sys

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.strategies.tita import compute_tita
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import run_backtest, StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct
from scripts.evaluate_strategy import aggregate

SYMBOLS = ["XLM/USDT", "DOGE/USDT", "SOL/USDT"]
BASELINE = {"alma_window": 9, "rsi_length": 14, "rsi_lower": 50, "rsi_upper": 55}
PERTS = [-20, -10, 0, 10, 20]
HOLDOUT_DAYS = 365
QUARTER_DAYS = 91

STOP_TARGET = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma",
                                atr_mult_stop=1.5)


def run_variant(df, param, value):
    params = dict(BASELINE)
    params[param] = value

    def signal_fn(d, p=params):
        d2 = compute_volatility(d.copy())
        return compute_tita(d2, alma_window=p["alma_window"], rsi_length=p["rsi_length"],
                             rsi_lower=p["rsi_lower"], rsi_upper=p["rsi_upper"])

    windows = run_walk_forward(df, signal_fn, "long_signal", None, RiskLimits(), STOP_TARGET,
                                window_days=180, step_days=180)
    agg = aggregate(windows)
    agg["chained_dd"] = round(chained_max_drawdown_pct(windows), 2)
    return agg


def sensitivity_sweep(symbol, df):
    print(f"\n--- Sensitivity sweep: {symbol} ---")
    cliff_flags = []
    for param, baseline_value in BASELINE.items():
        print(f"  {param} (baseline={baseline_value}):")
        pfs = []
        for pct in PERTS:
            value = baseline_value * (1 + pct / 100)
            if param in ("alma_window", "rsi_length"):
                value = max(2, round(value))
            agg = run_variant(df, param, value)
            pf = agg.get("profit_factor", float("nan"))
            pfs.append(pf if pf != float("inf") else None)
            label = "baseline" if pct == 0 else f"{pct:+d}%"
            print(f"    {label:>8} {value:>8.3f} trades={agg.get('total_trades', 0):>4} "
                  f"win%={agg.get('win_rate_pct', 0):>6} PF={pf} avgR={agg.get('avg_r_multiple', float('nan'))}")
        # crude cliff check: any neighbor-to-neighbor PF drop below 0.8 while
        # baseline itself was >=1.2 flags a potential cliff, worth a human look
        valid = [p for p in pfs if p is not None]
        if valid and max(valid) >= 1.2 and min(valid) < 0.8:
            cliff_flags.append(param)
    if cliff_flags:
        print(f"  ⚠️  Possible cliff(s) in: {', '.join(cliff_flags)} — result may be sensitive to exact params")
    else:
        print("  No cliffs detected across the 5x4 sweep for this symbol.")
    return cliff_flags


def holdout_check(symbol, df):
    print(f"\n--- Holdout validation: {symbol} ---")
    df = compute_volatility(df)
    signals = compute_tita(df)  # full-history warmup, unchanged from every prior TITA run

    latest = signals["dt"].max()
    holdout_start = latest - pd.Timedelta(days=HOLDOUT_DAYS)
    in_sample = signals[signals["dt"] < holdout_start]
    holdout = signals[signals["dt"] >= holdout_start].reset_index(drop=True)

    if len(in_sample) < 200 or len(holdout) < 200:
        print(f"  Skipped — insufficient history for a clean split "
              f"(in-sample={len(in_sample)}, holdout={len(holdout)} candles)")
        return None

    print(f"  in-sample:  {in_sample['dt'].iloc[0].date()} -> {in_sample['dt'].iloc[-1].date()} "
          f"({len(in_sample)} candles)")
    print(f"  holdout:    {holdout['dt'].iloc[0].date()} -> {holdout['dt'].iloc[-1].date()} "
          f"({len(holdout)} candles)")

    result = run_backtest(holdout, "long_signal", None, RiskLimits(), STOP_TARGET)
    wins = [t for t in result.trades if t.pnl > 0]
    losses = [t for t in result.trades if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    print(f"  HOLDOUT RESULT: {len(result.trades)} trades, PF={round(pf, 2) if result.trades else 'n/a'}, "
          f"win%={round(100 * len(wins) / len(result.trades), 1) if result.trades else 'n/a'}, "
          f"net%={round(result.net_return_pct, 2)}, maxDD%={round(result.max_drawdown_pct, 2)}")

    print("  per-quarter breakdown within holdout:")
    cursor = holdout_start
    quarters = []
    while cursor < latest:
        q_end = cursor + pd.Timedelta(days=QUARTER_DAYS)
        q_mask = (holdout["dt"] >= cursor) & (holdout["dt"] < q_end)
        q_df = holdout.loc[q_mask].reset_index(drop=True)
        if len(q_df) >= 10:
            q_result = run_backtest(q_df, "long_signal", None, RiskLimits(), STOP_TARGET)
            q_wins = [t for t in q_result.trades if t.pnl > 0]
            q_losses = [t for t in q_result.trades if t.pnl <= 0]
            q_gw = sum(t.pnl for t in q_wins)
            q_gl = abs(sum(t.pnl for t in q_losses))
            q_pf = q_gw / q_gl if q_gl > 0 else float("inf")
            quarters.append((cursor.date(), q_end.date(), len(q_result.trades), q_pf))
            print(f"    {cursor.date()} -> {q_end.date()}: {len(q_result.trades)} trades, "
                  f"PF={round(q_pf, 2) if q_result.trades else 'n/a'}, net%={round(q_result.net_return_pct, 2)}")
        cursor = q_end

    return {"trades": len(result.trades), "pf": pf, "win_pct": round(100 * len(wins) / len(result.trades), 1) if result.trades else None,
            "net_pct": result.net_return_pct, "quarters": quarters}


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    print("\n" + "=" * 90)
    print("TITA — sensitivity sweep + holdout validation for XLM/DOGE/SOL")
    print("=" * 90)

    summary = {}
    for symbol in SYMBOLS:
        df = md.get_ohlcv(symbol, "1d", 3000)
        cliffs = sensitivity_sweep(symbol, df)
        holdout = holdout_check(symbol, df)
        summary[symbol] = {"cliffs": cliffs, "holdout": holdout}

    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    for symbol, s in summary.items():
        h = s["holdout"]
        cliff_note = f"cliffs in {s['cliffs']}" if s["cliffs"] else "no cliffs"
        if h is None:
            print(f"  {symbol}: {cliff_note}; holdout skipped (insufficient history)")
        else:
            pf_str = round(h["pf"], 2) if h["pf"] != float("inf") else "inf"
            print(f"  {symbol}: {cliff_note}; holdout PF={pf_str}, {h['trades']} trades, "
                  f"win%={h['win_pct']}, net%={round(h['net_pct'], 2)}")


if __name__ == "__main__":
    main()
