# OKX Trading Bots

Five independent Python trading bots for OKX via [ccxt](https://github.com/ccxt/ccxt):

- [`okx_trend_bot.py`](#okx_trend_botpy) — SuperTrend + VWAP trend-following (with several optional/legacy
  signal modes: EMA stack, RSI/MACD cross, ADX regime filter, Stochastic).
- [`okx_zeefreaks_bot.py`](#okx_zeefreaks_botpy) — VWAP-cross + relative-volume + EMA(9/20) intraday day-trading bot.
- [`okx_ema_rsi_bot.py`](#okx_ema_rsi_botpy) — EMA(20/50/150/200) stack + RSI(14) 30/70 reversion bot.
- [`okx_orb_trend_bot.py`](#okx_orb_trend_botpy) — Opening-range breakout + daily-trend filter, max 1 trade/day/symbol.
- [`okx_scalper_bot.py`](#okx_scalper_botpy) — 1m momentum scalper with a pre-trade cost-vs-edge filter.

All five run backtests locally against real OKX history and can run paper,
OKX-demo, or live trading loops. They are fully independent — separate
config, state file, and log file — and none import each other.

**The trading logic in both is deliberately conservative and should not be
tuned to chase backtest results.** See [Validation pipeline](#validation-pipeline) below.

## okx_trend_bot.py

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
| `--backtest N` | Backtest the last N candles instead of running the live loop. Fetches history in paginated pages (OKX caps a single call at ~300 candles) so N is honored up to the symbol's actual listing history — the printed header shows the real candle count and date range used. |
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

- `--backtest N` walks backward through OKX's history page by page (~300
  candles per call) to assemble N candles. If the symbol's listing history
  is shorter than N, you get however much real history exists instead — the
  script prints a `NOTE:` line telling you the actual count, so check that
  rather than assuming N candles were used.
- Spot markets cannot short; `--allow-shorts` only takes effect on OKX swap
  markets.

---

## okx_zeefreaks_bot.py

A separate, intraday day-trading bot. Signal core is a systematic
approximation of the VWAP/volume-driven day-trading style associated with
the "Zeefreaks" trading approach — not a literal transcription of any
specific rule set:

- **VWAP cross** (session VWAP, resets every `--vwap-reset-hours`, default
  24h) is the entry trigger — the bot times the reclaim/rejection moment,
  not "currently above/below."
- **Relative volume** ("effort vs result"): the signal candle's volume must
  exceed `--volume-mult` (default 1.5x) its own rolling average, or the
  cross is ignored as unconfirmed.
- **EMA(fast)/EMA(slow)** (default 9/20) supplies trend bias; entries only
  fire in the direction the EMAs agree with.
- **`--max-hold-bars`** (default 24 bars = 6h on the default 15m timeframe)
  force-flattens a trade that overstays — day-trading discipline against a
  position quietly turning into a multi-day hold.

Shares the same cost model (taker fee, slippage) and circuit breakers
(consecutive-loss halt, daily loss limit, volatility-spike guard) as
`okx_trend_bot.py`, and the same paginated `--backtest` history fetch.

### CLI flags

| Flag | Description |
|---|---|
| `--backtest N` | Backtest the last N candles (paginated, same behavior as the trend bot). |
| `--live` / `--demo` | Same semantics as the trend bot — real orders vs. OKX sandbox. Requires the three `OKX_*` env vars. |
| `--allow-shorts` | Enable short entries (spot can't short; swap markets only). |
| `--timeframe TF` | Override candle timeframe (default `15m`). |
| `--symbol SYMBOL` | Override traded symbol (default `BTC/USDT`). |
| `--ema-fast` / `--ema-slow` | Override the EMA trend-bias lengths (default 9/20). |
| `--volume-mult` | Override the relative-volume confirmation multiplier (default 1.5). |
| `--vwap-reset-hours` | Override the VWAP session reset interval (default 24h). |
| `--max-hold-bars` | Override the forced-flatten bar count (0 disables). |

Run `python okx_zeefreaks_bot.py --help` for the authoritative, up-to-date list.

### Status

**Not validated yet.** First backtest (default config, BTC/USDT 15m, full
available ~31-day window): 95 trades, profit factor 0.33, fees consumed
104% of gross wins. This does not clear the same bar the trend bot is held
to (PF > 1.2, 20+ trades, consistent across symbols) — do not run
`--paper`/`--demo`/`--live` on this until it does.

---

## okx_ema_rsi_bot.py

A separate day-trading bot: pure EMA-stack trend filter + RSI(14) reversion
trigger, no other indicators.

- **EMA stack** (`--ema1`..`--ema4`, default 20/50/150/200): bullish when
  20>50>150>200, bearish when reversed. No ADX/strength filter — just the
  ordering, as specified.
- **RSI entry trigger**: long when RSI crosses below 30 (`--rsi-oversold`)
  *while the stack is bullish* (buying a dip within an established
  uptrend); short when RSI crosses above 70 (`--rsi-overbought`) while the
  stack is bearish (mirrored — shorting a rally within a downtrend). Spot
  can't short; requires `--allow-shorts` + OKX swap markets.
- **Exits are ATR stop/target only** (same 1.5x/2.5x framework as the other
  bots) — RSI crossing back the other way is not wired as a second exit
  signal. Flag it if you actually wanted an RSI-based exit instead.

### CLI flags

| Flag | Description |
|---|---|
| `--backtest N` | Backtest the last N candles (paginated, same behavior as the other two bots). |
| `--live` / `--demo` | Real orders vs. OKX sandbox. Requires the three `OKX_*` env vars. |
| `--allow-shorts` | Enable short entries (spot can't short; swap markets only). |
| `--timeframe TF` | Override candle timeframe (default `1h`). |
| `--symbol SYMBOL` | Override traded symbol (default `BTC/USDT`). |
| `--rsi-oversold` / `--rsi-overbought` | Override the RSI entry thresholds (default 30/70). |

Run `python okx_ema_rsi_bot.py --help` for the authoritative, up-to-date list.

### Status

**Not validated — and structurally rare.** Requiring a full 4-EMA bullish
stack *and* RSI<30 to occur on the same bar is a narrow intersection: deep
RSI oversold readings mostly happen during corrections/downtrends, which is
exactly when the bullish stack condition tends to break. Real-data results:

| Symbol | Timeframe | Window | Trades |
|---|---|---|---|
| BTC/USDT | 1h | ~125 days | 1 |
| BTC/USDT | 1d | 2018–2026 (full history) | 0 |
| ETH/USDT | 1h | ~125 days | 1 |
| ETH/USDT | 1d | 2018–2026 (full history) | 2 |
| SOL/USDT | 1h | ~125 days | 1 |
| SOL/USDT | 1d | 2020–2026 (full history) | 0 |

0–2 trades even across full multi-year history is not a sample size any
profit factor can be trusted from. Do not run `--paper`/`--demo`/`--live`
on this — there isn't enough evidence yet to call it anything at all.

---

## okx_orb_trend_bot.py

An original design (not a transcription of any named trader's style),
built specifically to work around the fee-bleed pattern seen in the other
bots here: **max one trade per day per symbol**.

- **Opening range**: each UTC day's high/low from `--session-start` (default
  12:00) for `--range-hours` (default 1h) — the Europe/US liquidity overlap.
- **Breakout entry**: long above the range high, short below the range low,
  later in the same session — gated by **daily EMA(50) trend** (no
  lookahead: only a fully-closed daily candle counts) and **relative
  volume** confirmation.
- **Exit**: stop at the opposite side of the range (ATR floor as backup for
  a degenerate tiny range), target = 2R, forced flatten at `--session-end`
  (default 21:00 UTC) regardless — genuine day-trading discipline, no
  overnight hold.

### CLI flags

| Flag | Description |
|---|---|
| `--backtest N` | Backtest the last N entry-timeframe candles (paginated). |
| `--live` / `--demo` | Real orders vs. OKX sandbox. Requires the three `OKX_*` env vars. |
| `--allow-shorts` | Enable short entries (spot can't short; swap markets only). |
| `--timeframe TF` | Override entry/opening-range timeframe (default `15m`). |
| `--symbol SYMBOL` | Override traded symbol (default `BTC/USDT`). |
| `--range-hours` | Override opening-range duration in hours (default 1). |
| `--session-start` / `--session-end` | Override the UTC session window (default 12/21). |
| `--volume-mult` | Override the relative-volume confirmation multiplier. |

Run `python okx_orb_trend_bot.py --help` for the authoritative, up-to-date list.

### Status

**Not validated — currently losing on all three symbols tested.**

| Symbol | Trades (31d) | Win rate | Profit factor | Fees % of gross win |
|---|---|---|---|---|
| BTC/USDT | 15 | 26.7% | 0.47 | 92.7% |
| ETH/USDT | 22 | 40.9% | 0.72 | 43.1% |
| SOL/USDT | 15 | 33.3% | 0.74 | 37.6% |

Consistent across symbols, but consistently unprofitable. Notably, most
exits are `session_close` (forced flatten), not `stop` or `tp` — most
breakouts here don't move decisively either way before end of session,
which suggests the 2R target may be too far for typical intraday
continuation on these symbols/timeframe. That's a real lead for further
investigation, not something I've acted on — do not run
`--paper`/`--demo`/`--live` on this until it clears the same bar as the
others (PF > 1.2, 20+ trades, consistent across symbols).

---

## okx_scalper_bot.py

An original design (my own), built specifically to confront the fee-bleed
problem head-on rather than just document it: EMA(5/13) momentum cross on
a 1m chart, gated by relative volume, a liquidity-hours filter, and — the
core idea — **a pre-trade cost filter**: the expected target move (ATR x
the configured take-profit multiple, as % of price) must exceed
`--min-edge-ratio` (default 3x) the round-trip fee+slippage cost, or the
bot refuses to trade regardless of signal quality.

### CLI flags

| Flag | Description |
|---|---|
| `--backtest N` | Backtest the last N candles (paginated). |
| `--live` / `--demo` | Real orders vs. OKX sandbox. Requires the three `OKX_*` env vars. |
| `--allow-shorts` | Enable short entries (spot can't short; swap markets only). |
| `--timeframe TF` | Override timeframe (default `1m`). |
| `--symbol SYMBOL` | Override traded symbol (default `BTC/USDT`). |
| `--min-edge-ratio` | Override the required expected-move-to-cost ratio (default 3.0). |
| `--volume-mult` | Override the relative-volume confirmation multiplier. |
| `--max-hold-bars` | Override the forced-flatten bar count (default 10 = 10 minutes). |

Run `python okx_scalper_bot.py --help` for the authoritative, up-to-date list.

### Status — the cost filter found something more fundamental than a bad backtest

At the default 3x margin: **0 trades** over ~2 days of 1m BTC/USDT (300
real 1m candles is the deepest OKX granular history reachable here). Not a
signal problem — diagnosed directly: median expected move (1.5x ATR) on 1m
BTC is ~0.033% of price, max observed ~0.41%, while OKX's round-trip taker
cost alone is ~0.25%. Even relaxing the filter to 1.0x (target *exactly*
equals cost, zero margin — a diagnostic setting, not a recommendation)
produces just **1 trade**, whose "win" still cost more in fees than it
net-made.

**Conclusion: pure 1-minute scalping on OKX spot with market/taker orders
is not a parameter-tuning problem — the typical achievable move at that
timeframe is arithmetically smaller than the cost of taking it.** Anything
that would change this is a different bot entirely: maker/limit orders
(lower/rebated fees, but adds fill uncertainty), a higher OKX fee tier, a
much more volatile symbol, or a longer holding timeframe (at which point
it's not really scalping). I have not built any of those — flag which
direction you want if you'd like to pursue it. Do not run
`--paper`/`--demo`/`--live` on this as-is.
