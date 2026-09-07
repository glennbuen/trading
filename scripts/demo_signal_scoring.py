#!/usr/bin/env python3
"""
Demonstrates cryptobot/scoring.py against Breakout+Retest's real
historical signals (architecture spec §14's worked example, applied to
real data instead of illustration numbers).

This does NOT change how Breakout+Retest decides to enter a trade — that
logic (Phase 4) is untouched, and its rejection (Phase 6) stands. Scoring
is computed here purely for illustration/journaling: "every trade must
explain its score" (§31), demonstrated against signals the strategy
already produced.

Usage:
    python scripts/demo_signal_scoring.py
"""

import sys

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.price_action import compute_price_action
from cryptobot.engines.market_structure import compute_market_structure
from cryptobot.engines.volume import compute_volume
from cryptobot.engines.liquidity import compute_liquidity
from cryptobot.strategies.breakout_retest import compute_breakout_retest
from cryptobot.backtest.engine import StopTargetConfig, _compute_stop
from cryptobot.scoring import SignalInputs, score_signal, ScoringWeights

SYMBOL, TIMEFRAME, CANDLES = "BTC/USDT", "1h", 8000
STOP_TARGET = StopTargetConfig(method="atr", atr_mult_stop=1.5, target_r_multiple=2.0)


def extract_inputs(d: pd.DataFrame, i: int, side: str) -> SignalInputs:
    row = d.iloc[i]
    next_row = d.iloc[i + 1]
    entry = next_row["open"]
    stop = _compute_stop(row, entry, side, STOP_TARGET)
    risk_dist = abs(entry - stop)
    target = (entry + risk_dist * STOP_TARGET.target_r_multiple if side == "long"
              else entry - risk_dist * STOP_TARGET.target_r_multiple)

    if side == "long":
        breakout_in_direction = bool(row["pa_breakout_up"])
        confirming_candle = bool(row["pa_strong_bullish"] or row["pa_bullish_rejection"])
        liquidity_sweep = bool(row["liq_sweep_reversal_bullish"])
        equal_level = bool(row["liq_equal_lows"])
    else:
        breakout_in_direction = bool(row["pa_breakout_down"])
        confirming_candle = bool(row["pa_strong_bearish"] or row["pa_bearish_rejection"])
        liquidity_sweep = bool(row["liq_sweep_reversal_bearish"])
        equal_level = bool(row["liq_equal_highs"])

    return SignalInputs(
        symbol=SYMBOL, side=side, setup_label="Breakout + Retest",
        trend_state=row["ms_trend_state"], breakout_in_direction=breakout_in_direction,
        confirming_candle=confirming_candle, relative_volume=row["vol_relative"],
        liquidity_sweep=liquidity_sweep, equal_level=equal_level,
        entry=entry, stop=stop, target=target,
    )


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    print(f"Fetching {SYMBOL} {TIMEFRAME} ({CANDLES} candles)...", file=sys.stderr)
    df = md.get_ohlcv(SYMBOL, TIMEFRAME, CANDLES)

    d = compute_volatility(df.copy())
    d = compute_price_action(d)
    d = compute_market_structure(d)
    d = compute_volume(d)
    d = compute_liquidity(d)
    d = compute_breakout_retest(d)

    scores = []
    n = len(d)
    for i in range(1, n - 1):
        row = d.iloc[i]
        if bool(row.get("br_long_entry_signal", False)):
            scores.append(score_signal(extract_inputs(d, i, "long")))
        elif bool(row.get("br_short_entry_signal", False)):
            scores.append(score_signal(extract_inputs(d, i, "short")))

    print(f"\n{len(scores)} total signals scored ({SYMBOL} {TIMEFRAME}, {n} candles)\n")

    print("=" * 60)
    print("EXAMPLE SCORE BREAKDOWNS (3 real historical signals)")
    print("=" * 60)
    for s in scores[:3]:
        print()
        print(s.explain())

    print("\n" + "=" * 60)
    print("SCORE DISTRIBUTION")
    print("=" * 60)
    totals = [s.total_score for s in scores]
    series = pd.Series(totals)
    print(series.describe())
    for threshold in [50, 60, 70, 80]:
        n_clear = sum(1 for t in totals if t >= threshold)
        print(f"  >= {threshold}/100: {n_clear}/{len(totals)} ({n_clear/len(totals)*100:.1f}%)")

    print("\n" + "=" * 60)
    print("NOTE ON THE RISK/REWARD COMPONENT")
    print("=" * 60)
    rr_values = set(round(s.r_multiple, 3) for s in scores)
    print(f"Distinct R-multiple values across all {len(scores)} signals: {rr_values}")
    print("Breakout+Retest uses a FIXED target_r_multiple (2.0) — every signal's planned")
    print("R/R is therefore identical, so its risk_reward SCORE COMPONENT carries zero")
    print("discriminating information here. This isn't a scoring-system limitation, it's")
    print("a property of this strategy's fixed-R exit design — a strategy with a variable,")
    print("structure-based target (e.g. Phase 11's remaining strategies) would show real")
    print("variation in this component. Documented honestly rather than glossed over.")


if __name__ == "__main__":
    main()
