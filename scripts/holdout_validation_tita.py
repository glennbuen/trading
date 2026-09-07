#!/usr/bin/env python3
"""
TITA held-out validation — the one gap named in every prior TITA
evaluation doc ("no true out-of-sample holdout beyond the walk-forward
windows themselves... a genuinely untouched final holdout period hasn't
been reserved").

IMPORTANT HONESTY NOTE, stated up front: this is the best approximation
of a holdout this project can construct from ALREADY-FETCHED historical
data — it is NOT a truly prospective test. Every prior TITA walk-forward
run fetched "the most recent 3000 daily candles", which already included
whatever the most recent ~12 months looked like at the time it was run;
that stretch contributed to the aggregate PF=1.83 result that got TITA
selected as this project's one genuine lead in the first place. Isolating
it now and reporting it separately is still useful (it directly answers
"does TITA's edge look any different when the most recent stretch is
judged on its own, not blended into an 8-year aggregate"), but it is not
a substitute for genuine forward validation — that is exactly what paper
trading itself provides once started, which is why this script's own
result is a precondition for starting paper trading, not a replacement
for it.

Method: fetch the full history (same 3000-candle 1d pull as every prior
TITA run), compute TITA's signal ONCE on the full series (correct
warmup, unchanged from every prior evaluation), then split chronologically
at (latest date - 365 days). Report the holdout slice's result on its
own, plus a finer per-quarter breakdown to check for the same kind of
thin-sample artifact this project has flagged in every other strategy.
No parameter is touched — same TITA defaults, same stop mechanism, same
costs/risk config as every prior TITA run.
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
from scripts.evaluate_strategy import aggregate

HOLDOUT_DAYS = 365
QUARTER_DAYS = 91


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)
    stop_target = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma",
                                    atr_mult_stop=1.5)

    print("\n" + "=" * 78)
    print(f"TITA HELD-OUT VALIDATION — most recent {HOLDOUT_DAYS} days, isolated")
    print("=" * 78)

    for symbol in ["BTC/USDT", "ETH/USDT"]:
        df = md.get_ohlcv(symbol, "1d", 3000)
        df = compute_volatility(df)
        signals = compute_tita(df)  # full-history warmup, exactly as every prior TITA run

        latest = signals["dt"].max()
        holdout_start = latest - pd.Timedelta(days=HOLDOUT_DAYS)
        in_sample = signals[signals["dt"] < holdout_start]
        holdout = signals[signals["dt"] >= holdout_start].reset_index(drop=True)

        print(f"\n--- {symbol} ---")
        print(f"  in-sample:  {in_sample['dt'].iloc[0].date()} -> {in_sample['dt'].iloc[-1].date()} "
              f"({len(in_sample)} candles)")
        print(f"  holdout:    {holdout['dt'].iloc[0].date()} -> {holdout['dt'].iloc[-1].date()} "
              f"({len(holdout)} candles)")

        result = run_backtest(holdout, "long_signal", None, RiskLimits(), stop_target)
        wins = [t for t in result.trades if t.pnl > 0]
        losses = [t for t in result.trades if t.pnl <= 0]
        gross_win = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
        print(f"  HOLDOUT RESULT: {len(result.trades)} trades, PF={round(pf, 2) if result.trades else 'n/a'}, "
              f"win%={round(100*len(wins)/len(result.trades), 1) if result.trades else 'n/a'}, "
              f"net%={round(result.net_return_pct, 2)}, maxDD%={round(result.max_drawdown_pct, 2)}")

        # quarterly breakdown within the holdout, to check for thin-sample artifacts
        print("  per-quarter breakdown within holdout:")
        cursor = holdout_start
        while cursor < latest:
            q_end = cursor + pd.Timedelta(days=QUARTER_DAYS)
            q_mask = (holdout["dt"] >= cursor) & (holdout["dt"] < q_end)
            q_df = holdout.loc[q_mask].reset_index(drop=True)
            if len(q_df) >= 10:
                q_result = run_backtest(q_df, "long_signal", None, RiskLimits(), stop_target)
                q_wins = [t for t in q_result.trades if t.pnl > 0]
                q_losses = [t for t in q_result.trades if t.pnl <= 0]
                q_gw = sum(t.pnl for t in q_wins)
                q_gl = abs(sum(t.pnl for t in q_losses))
                q_pf = q_gw / q_gl if q_gl > 0 else float("inf")
                print(f"    {cursor.date()} -> {q_end.date()}: {len(q_result.trades)} trades, "
                      f"PF={round(q_pf, 2) if q_result.trades else 'n/a'}, net%={round(q_result.net_return_pct, 2)}")
            cursor = q_end


if __name__ == "__main__":
    main()
