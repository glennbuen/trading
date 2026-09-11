#!/usr/bin/env python3
"""
TITA backtest — top-20-by-market-cap coins (ex-stablecoins), 2026-09-11.

Prompted by: "we can screen crypto with tita? coinmarketcap.com" — the
answer given at the time was that TITA's edge (PF 2.60 BTC / 1.79 ETH,
docs/TITA_HOLDOUT_VALIDATION.md) is validated ONLY on BTC/USDT and
ETH/USDT; running the same signal against a new symbol is a fresh,
unvalidated hypothesis, not something that inherits BTC/ETH's evidence.
This script runs that fresh hypothesis properly: the SAME unchanged TITA
signal (alma_window=9, rsi_length=14, rsi_lower=50, rsi_upper=55), the
SAME StopTargetConfig (trailing_indicator on tita_alma, atr_mult_stop=1.5)
and RiskLimits() defaults, and the SAME walk-forward methodology
(3000 daily candles, 180-day windows) used for every prior TITA
evaluation in this project — nothing tuned, nothing given an easier bar.

Universe: top 20 coinmarketcap.com ranks as of 2026-09-11, MINUS 5
stablecoins that were in that top-20 (USDT, USDC, USDe, DAI, USD1) — a
long-only momentum strategy has no meaningful signal on an asset pegged
to $1, so backtesting them would be a null result by construction, not
a finding. That leaves 15 directional symbols, listed below with their
CoinMarketCap rank at fetch time. BTC/ETH are included again here (not
skipped) as an in-run consistency check against the already-published
holdout numbers.

Symbols not tradeable as a *_USDT spot pair on OKX (this project's one
data source, per every existing script) are skipped with a note printed,
not silently dropped — e.g. LEO (Bitfinex's own exchange token) is not
expected to be listed on OKX.
"""

import sys
sys.path.insert(0, '.')

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.strategies.tita import compute_tita
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.backtest.walk_forward import run_walk_forward, chained_max_drawdown_pct
from scripts.evaluate_strategy import aggregate

# (symbol, coinmarketcap rank at fetch time 2026-09-11)
CANDIDATES = [
    ("BTC/USDT", 1), ("ETH/USDT", 2), ("BNB/USDT", 4), ("XRP/USDT", 5),
    ("SOL/USDT", 7), ("TRX/USDT", 8), ("HYPE/USDT", 9), ("ZEC/USDT", 10),
    ("DOGE/USDT", 11), ("XMR/USDT", 12), ("LINK/USDT", 13), ("LEO/USDT", 14),
    ("ADA/USDT", 15), ("XLM/USDT", 16), ("BCH/USDT", 20),
]

STOP_TARGET = StopTargetConfig(method="trailing_indicator",
                                trailing_indicator_col="tita_alma", atr_mult_stop=1.5)


def signal_fn(df):
    d = compute_volatility(df.copy())
    return compute_tita(d)


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    results = []
    skipped = []

    for symbol, rank in CANDIDATES:
        try:
            df = md.get_ohlcv(symbol, "1d", 3000)
        except Exception as e:
            skipped.append((symbol, rank, str(e)))
            continue
        if df is None or len(df) < 200:
            skipped.append((symbol, rank, f"insufficient history ({0 if df is None else len(df)} candles)"))
            continue

        windows = run_walk_forward(df, signal_fn, "long_signal", None,
                                    RiskLimits(), STOP_TARGET,
                                    window_days=180, step_days=180)
        agg = aggregate(windows)
        agg["symbol"] = symbol
        agg["rank"] = rank
        agg["candles"] = len(df)
        agg["span"] = f"{df['dt'].iloc[0].date()} -> {df['dt'].iloc[-1].date()}"
        agg["chained_dd"] = round(chained_max_drawdown_pct(windows), 2)
        results.append(agg)

    print("\n" + "=" * 100)
    print("TITA — top-20-by-market-cap backtest (ex-stablecoins), unchanged signal/stop/risk params")
    print("=" * 100)
    print(f"{'Rank':>4} {'Symbol':<10} {'Candles':>8} {'Span':<24} {'Trades':>7} "
          f"{'Win%':>6} {'PF':>7} {'AvgR':>7} {'ChainDD%':>9}")
    for r in sorted(results, key=lambda x: x["rank"]):
        trades = r.get("total_trades", 0)
        if trades == 0:
            print(f"{r['rank']:>4} {r['symbol']:<10} {r['candles']:>8} {r['span']:<24} {'0':>7}  -- no trades in sample --")
            continue
        pf = r.get("profit_factor")
        pf_str = f"{pf:.2f}" if pf != float("inf") else "inf"
        print(f"{r['rank']:>4} {r['symbol']:<10} {r['candles']:>8} {r['span']:<24} {trades:>7} "
              f"{r['win_rate_pct']:>6} {pf_str:>7} {r['avg_r_multiple']:>7} {r['chained_dd']:>9}")

    if skipped:
        print("\nSkipped (not available on OKX or insufficient history):")
        for symbol, rank, reason in skipped:
            print(f"  rank {rank:>2} {symbol:<10} — {reason}")

    print("\nReference — already-published holdout (docs/TITA_HOLDOUT_VALIDATION.md), "
          "different window scheme (365-day single holdout, not 180-day walk-forward), "
          "not directly comparable row-for-row to the table above:")
    print("  BTC/USDT: PF=2.60, Win%=43.8, 16 trades (2025-09-07 -> 2026-09-07)")
    print("  ETH/USDT: PF=1.79, Win%=30.0, 20 trades (2025-09-07 -> 2026-09-07)")


if __name__ == "__main__":
    main()
