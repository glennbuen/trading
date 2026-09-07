#!/usr/bin/env python3
"""
TITA paper-trading check — the live/paper stage of this project's
5-stage validation pipeline (backtest -> paper -> demo -> live),
following TITA's held-out-validation pass (docs/TITA_HOLDOUT_VALIDATION.md).

Designed to be invoked ONCE PER DAY, shortly after each new UTC daily
candle opens (i.e. shortly after the PREVIOUS day's candle has fully
closed) — e.g. via a daily cron job. Re-running it more than once on the
same day is harmless (paper_trading.engine's `last_processed_ts` makes a
same-bar re-check a no-op, verified in tests/test_paper_trading.py).

No real orders are placed and no API credentials are required — this
reads only public market data (OHLCV + ticker) from OKX and simulates
fills against them, tracking its own equity/trade ledger in a local JSON
file per symbol. This is deliberately simpler and safer than OKX's own
demo-trading sandbox (stage 3 of the pipeline): no account, no API keys,
nothing that could ever place a real order even by mistake. Promoting to
demo/live is a separate, later, explicit decision — not something this
script does on its own.

Same TITA parameters, stop mechanism, and cost assumptions as every
prior TITA evaluation and the holdout validation — nothing tuned here.

Usage:
    python scripts/run_tita_paper_trading.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.engines.volatility import compute_volatility
from cryptobot.strategies.tita import compute_tita
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.backtest.engine import StopTargetConfig
from cryptobot.data.exchange import timeframe_to_ms
from cryptobot.paper_trading.state import load_state, save_state
from cryptobot.paper_trading.engine import check_and_update

SYMBOLS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAME = "1d"
STATE_DIR = Path("paper_trading_state")
STARTING_EQUITY = 1000.0

STOP_TARGET = StopTargetConfig(method="trailing_indicator", trailing_indicator_col="tita_alma",
                                atr_mult_stop=1.5)
RISK_LIMITS = RiskLimits()


def signal_fn(df: pd.DataFrame) -> pd.DataFrame:
    d = compute_volatility(df.copy())
    return compute_tita(d)


def run_for_symbol(ex: ExchangeProvider, md: MarketDataProvider, symbol: str) -> dict:
    state_path = str(STATE_DIR / f"tita_{symbol.replace('/', '_')}.json")
    state = load_state(state_path, symbol=symbol, strategy="tita", starting_equity=STARTING_EQUITY)

    df = md.get_recent_ohlcv(symbol, TIMEFRAME, limit=300)  # ample warmup for ALMA(9)/RSI(14)
    signals = signal_fn(df)

    live_price = md.get_last_price(symbol)
    now_ms = ex.milliseconds()
    live_dt = pd.Timestamp(now_ms, unit="ms", tz="UTC")

    result = check_and_update(
        state, signals, timeframe_to_ms(TIMEFRAME), now_ms,
        long_col="long_signal", short_col=None, stop_target=STOP_TARGET,
        risk_limits=RISK_LIMITS, live_price=live_price, live_dt=live_dt,
    )
    save_state(state, state_path)
    return {"symbol": symbol, "result": result, "state": state}


def print_report(outcomes: list[dict]):
    print("\n" + "=" * 78)
    print("TITA PAPER TRADING — daily check")
    print("=" * 78)
    for o in outcomes:
        symbol, result, state = o["symbol"], o["result"], o["state"]
        print(f"\n--- {symbol} ---")
        print(f"  action: {result['action']}")
        if result["action"] == "entered":
            print(f"  entered {result['side']} @ {result['entry_price']:.2f}, "
                  f"stop={result['stop']:.2f}, size={result['size']:.6f}")
        elif result["action"] == "exited":
            t = result["trade"]
            print(f"  closed {t['side']} @ {t['exit_price']:.2f} ({t['exit_reason']}), "
                  f"pnl={t['pnl']:.2f}, R={t['r_multiple']:.2f}")
        elif result["action"] == "signal_rejected":
            print(f"  signal seen ({result.get('side')}) but rejected: {result.get('reason')}")
        print(f"  equity: {state.risk.equity if state.risk else state.starting_equity:.2f}   "
              f"open_position: {'yes' if state.position else 'no'}   "
              f"total_trades_so_far: {len(state.trades)}")


def main():
    ex = ExchangeProvider(exchange_id="okx")  # public data only, no credentials needed
    md = MarketDataProvider(ex)
    outcomes = [run_for_symbol(ex, md, symbol) for symbol in SYMBOLS]
    print_report(outcomes)


if __name__ == "__main__":
    main()
