#!/usr/bin/env python3
"""
Per-window trade-count check for the strategies whose PF crossed the
1.2-on-both-symbols bar under exit_rules_spec.md's new exit system
(scripts/retest_all_with_exit_rules.py) — the same thin-sample-artifact
check applied to every "promising" result throughout this project,
before trusting an aggregate PF number. flat_lock variant only (the
variant that performs better across the suite overall — see
docs/EVALUATION_EXIT_RULES_RETEST.md).

Usage: python scripts/exit_rules_per_window_check.py
"""

import sys

sys.path.insert(0, ".")

from cryptobot.data.exchange import ExchangeProvider
from cryptobot.data.market_data import MarketDataProvider
from cryptobot.risk.risk_manager import RiskLimits
from cryptobot.engines.volatility import compute_volatility
from cryptobot.engines.parabolic_risk import compute_parabolic_risk
from cryptobot.backtest.exit_rules import ExitRulesConfig, attach_exit_indicators
from cryptobot.backtest.exit_rules_engine import run_backtest_with_exit_rules
from cryptobot.backtest.walk_forward import run_walk_forward
from cryptobot.strategies.spyfrat_system import bollinger_breakout_up
from scripts.retest_all_with_exit_rules import STRATEGIES

CFG = ExitRulesConfig(enable_atr_trailing_above_lock=False)


def dump(md, name, symbol, long_col, short_col, signal_fn):
    df = md.get_ohlcv(symbol, "1d", 3000)

    def wrapped(d, _fn=signal_fn, _cfg=CFG):
        return _fn(d, exit_cfg=_cfg)

    windows = run_walk_forward(df, wrapped, long_col, short_col, RiskLimits(), CFG,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    print(f"\n--- {name} {symbol} (flat_lock) ---")
    for w in windows:
        r = w.result
        print(f"  {w.label}: {r.num_trades} trades, PF={r.profit_factor}, win%={r.win_rate_pct}, net%={r.net_return_pct}")


def dump_spyfrat(md, symbol):
    daily = md.get_ohlcv(symbol, "1d", 3000)
    weekly = md.get_ohlcv(symbol, "1w", 500)
    pre_merged = compute_parabolic_risk(daily, weekly, rsi_length=30)

    def signal_fn(d, _cfg=CFG):
        d2 = compute_volatility(d.copy())
        d2["long_signal"] = bollinger_breakout_up(d2, 50, 0.20)
        d2 = attach_exit_indicators(d2, _cfg)
        return d2

    windows = run_walk_forward(pre_merged, signal_fn, "long_signal", None, RiskLimits(), CFG,
                                window_days=180, step_days=180, backtest_fn=run_backtest_with_exit_rules)
    print(f"\n--- SPYFRAT Core System {symbol} (flat_lock) ---")
    for w in windows:
        r = w.result
        print(f"  {w.label}: {r.num_trades} trades, PF={r.profit_factor}, win%={r.win_rate_pct}, net%={r.net_return_pct}")


def main():
    ex = ExchangeProvider(exchange_id="okx")
    md = MarketDataProvider(ex)

    for name in ["Breakout (A)", "Ichimoku Cross", "TITA", "MAMA"]:
        signal_fn, long_col, short_col = STRATEGIES[name]
        for symbol in ["BTC/USDT", "ETH/USDT"]:
            dump(md, name, symbol, long_col, short_col, signal_fn)

    for symbol in ["BTC/USDT", "ETH/USDT"]:
        dump_spyfrat(md, symbol)


if __name__ == "__main__":
    main()
