# OKX Trend Bot

A Python trading bot for BTC/USDT (and other pairs) on OKX via [ccxt](https://github.com/ccxt/ccxt).
Signal engine is SuperTrend + VWAP (with several optional/legacy modes: EMA stack,
RSI/MACD cross, ADX regime filter, Stochastic). Runs backtests locally and can
run paper, OKX-demo, or live trading loops.

**The trading logic is deliberately conservative and should not be tuned to
chase backtest results.** See [Validation pipeline](#validation-pipeline) below.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in real values; .env is gitignored, never commit it
```

Required env vars (only needed for `--live` / `--demo`):

- `OKX_API_KEY`
- `OKX_API_SECRET`
- `OKX_PASSPHRASE`

## CLI flags

| Flag | Description |
|---|---|
| `--backtest N` | Backtest the last N candles instead of running the live loop. Note: candle count is capped at 1000 regardless of N (see [Known limits](#known-limits)). |
| `--live` | Place real orders on OKX. Requires typing `CONFIRM` at a prompt and the three `OKX_*` env vars. |
| `--demo` | Route orders to the OKX demo/sandbox environment (virtual funds). Requires the three `OKX_*` env vars. |
| `--day` | Day-trading preset: 1h timeframe, tighter ATR stop/TP multiples, looser ADX threshold, shorter cooldown. |
| `--minimal` | Signal mode reduced to SuperTrend (trend timing) + VWAP (participation) only — no EMA stack, RSI, MACD, Stochastic, or ADX. |
| `--adaptive-st` | Volatility-adaptive SuperTrend ATR multiplier (widens in choppy conditions, tightens in calm ones) instead of a fixed multiplier. |
| `--vwap-bands` | Require price beyond a VWAP standard-deviation band, not just past the VWAP line. |
| `--signal-mode {trend,oscillator,dip,pullback,supertrend}` | Selects the entry-logic mode (ignored when `--minimal` is set). |
| `--exit-mode {fixed,trailing,hybrid}` | Overrides the exit behavior: fixed ATR target, Chandelier-style trailing stop, or partial-at-target + trail the rest. |
| `--volume-filter` | Require above-average volume on the signal candle. |
| `--vwap-filter` | Require price above/below VWAP for long/short entries (legacy filter, separate from `--vwap-bands`). |
| `--mtf` | Multi-timeframe mode: 1h regime filter, 15m entry timing, with no-lookahead alignment. |
| `--allow-shorts` | Enable short entries. Spot markets can't actually short — only meaningful on OKX swap markets. |
| `--timeframe TF` | Override the candle timeframe (e.g. `1h`, `4h`, `1d`). |
| `--symbol SYMBOL` | Override the traded symbol (e.g. `BTC/USDT`, `ETH/USDT`). |

Run `python okx_trend_bot.py --help` for the authoritative, up-to-date list.

## Validation pipeline

The bot is meant to be proven out in stages, in order. Do not skip a stage,
and do not tune parameters to force a later stage to look good — a strategy
that only "works" after fitting to its own backtest is not a real edge.

1. **Backtest** — `python okx_trend_bot.py --backtest 3000 --day --minimal --adaptive-st`
   Local simulation against historical OHLCV pulled from OKX. No money at risk.
   Look for profit factor > 1.2 with 20+ trades, holding up consistently
   across multiple symbols with the *same* parameters (no per-symbol tuning).
2. **Paper** — `python okx_trend_bot.py --day --minimal --adaptive-st`
   Live market data, simulated fills, no exchange account needed. Confirms the
   signal/exit logic behaves the same way outside the backtest loop.
3. **Demo** — `python okx_trend_bot.py --demo --day --minimal --adaptive-st`
   Routes real orders to OKX's sandbox (`x-simulated-trading` header), using
   virtual funds. Requires `OKX_API_KEY` / `OKX_API_SECRET` / `OKX_PASSPHRASE`.
   Confirms order placement, sizing, and exchange integration end-to-end
   without financial risk.
4. **Live** — `python okx_trend_bot.py --live --day --minimal --adaptive-st`
   Real orders, real funds. Requires typing `CONFIRM` at a prompt in addition
   to the env vars. Start small.

Only advance a stage once the previous one has behaved as expected for a
reasonable observation period.

## Safety features

- Circuit breakers: halts new entries after `max_consecutive_losses` stop-outs
  in a row, or after equity drops more than `daily_loss_limit_pct` in ~24h.
- Volatility spike guard: skips new entries when ATR blows out vs its own
  recent average (crash/cascade conditions).
- Breakeven stop and optional Chandelier-style trailing stop to lock in gains.
- Position sizing is capped by both `risk_per_trade_pct` and
  `max_position_pct` of equity.
- `--live` requires an explicit typed `CONFIRM`; `--demo` only ever touches
  OKX's sandbox environment.

## Known limits

- `--backtest N` caps the requested candle count at 1000 in code
  (`min(args.backtest, 1000)`), separately from whatever OKX's API itself
  returns/paginates. Requesting `--backtest 3000` will only ever backtest
  1000 candles — check the printed candle count and date range in the
  backtest header rather than assuming N candles were used.
- Spot markets cannot short; `--allow-shorts` only takes effect on OKX swap
  markets.
