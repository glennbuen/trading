# Paper Trading — TITA (stage 2 of 5: backtest → **paper** → demo → live)

## What this is

A daily check script (`scripts/run_tita_paper_trading.py`) that simulates
TITA trading BTC/USDT and ETH/USDT in real time, using real live OKX
market data, without placing any real orders or touching an exchange
account at all. It reads only public data (recent candles + a live
ticker price) and keeps its own equity/trade ledger in local JSON files.
No API keys, no credentials, no way for it to accidentally place a real
order — a deliberately safer first step than OKX's own demo-trading
sandbox (stage 3).

## How to run it

```
python scripts/run_tita_paper_trading.py
```

Run it **once per day**, any time after each new UTC daily candle opens
(i.e. after the previous day's candle has fully closed) — a daily cron
job is the intended usage. Running it more than once on the same day is
harmless: it detects the candle it already processed and reports
`already_processed` without touching anything.

Example cron entry (adjust the path):
```
5 0 * * * cd /workspaces/trading && python3 scripts/run_tita_paper_trading.py >> paper_trading_state/tita.log 2>&1
```

## Where the state lives

`paper_trading_state/tita_BTC_USDT.json` and `tita_ETH_USDT.json`
(gitignored — this is live operational state, not something to commit).
Each file holds: the current open position (if any), the full trade
history so far, the simulated equity, and a snapshot of the
`RiskManager`'s internal state (day/week loss tracking, consecutive-loss
halt, exposure) so gating behaves identically to backtesting across
restarts. Delete a file to reset that symbol's paper-trading run from
scratch — do this deliberately, not by accident.

## What it uses, unchanged from every prior TITA evaluation

Same defaults (`alma_window=9, rsi_length=14, rsi_lower=50,
rsi_upper=55`), same exit mechanism (`trailing_indicator` on `tita_alma`
with an ATR(1.5x) hard-floor stop underneath), same cost assumptions
(`BacktestCosts` defaults — 0.10% taker fee, 0.05% entry slippage, 0.4%
stop slippage). **These are the parameters that produced the validated
holdout result** (`docs/TITA_HOLDOUT_VALIDATION.md` — PF 2.60 BTC / 1.79
ETH) and are deliberately never touched here without a full re-run.

## Risk limits — tightened 2026-09-11, account-level only

`RiskLimits` (position sizing, daily/weekly loss circuit breakers,
consecutive-loss halt, exposure caps) is **no longer the shared
`RiskLimits()` default** every other strategy's backtest script uses —
`scripts/run_tita_paper_trading.py` now passes a stricter override,
prompted by comparing this project's discretionary PSE/US-stocks risk
rules (`pse/WATCHLIST.md`, `us-stocks/WATCHLIST.md`) against crypto's
higher volatility:

| Limit | Shared default | TITA paper-trading override |
|---|---|---|
| Risk per trade | 0.5% of equity | **0.3%** |
| Max daily loss | 2.0% | **1.5%** |
| Max weekly loss | 5.0% | **3.5%** |
| Consecutive-loss halt trigger | 3 losses | **2 losses** |
| Halt cooldown | 24h | **48h** |
| Max exposure / position size | 25% | **20%** |

This layer sits *outside* the backtested signal/exit logic — it only
scales dollar position size and gates when new trades are allowed, so
tightening it doesn't touch the trade-by-trade R-multiple distribution
the holdout PF was computed from. It's safe to change without
re-validating, unlike `STOP_TARGET`'s `atr_mult_stop`/`target_r_multiple`
above. Applied while both symbols were still at zero paper trades (see
`paper_trading_state/*.json`), so nothing already-recorded was
retroactively affected. The shared `RiskLimits()` default used by every
other strategy's evaluation script under `scripts/` is untouched.

## How to check on it

Just run the script — it prints a report each time (current action,
equity, whether a position is open, total trades so far). For a fuller
look, read the JSON state files directly, or write a small script that
loads them via `cryptobot.paper_trading.state.load_state` and computes
the same profit-factor/win-rate metrics used throughout this project's
other evaluations, once enough trades have accumulated.

## What "success" looks like, and what comes next

TITA trades roughly once every 2-4 weeks on daily bars (16-20 trades/
year per the holdout validation), so a meaningful paper-trading sample
will take months to accumulate, not days. The honest next decision point
is: once enough paper trades exist to say something statistically
non-trivial (this project's own standard elsewhere has generally wanted
double-digit trade counts per leg before drawing a conclusion), compare
the paper-trading PF/win-rate/avg-R against the backtest and holdout
numbers. A result that's roughly consistent (not necessarily identical —
paper trading has its own real-time execution nuances, e.g. exact
timing of the daily check relative to the candle close) supports
promoting TITA to OKX's demo-trading sandbox (stage 3, not yet built);
a result that diverges sharply is itself important information, not a
failure to paper over.
