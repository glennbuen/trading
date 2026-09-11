# Crypto Chart Watchlist — Discretionary, Separate From TITA

**This is a different track from `cryptobot/`'s TITA strategy, not a
replacement for it.** TITA is this project's one validated systematic
strategy (backtest → walk-forward → sensitivity sweep → holdout →
paper trading, see `docs/TITA_HOLDOUT_VALIDATION.md` and
`docs/PAPER_TRADING.md`) — it trades on its own rules, no chart-reading
judgment involved. This file is the discretionary counterpart, ported
from `pse/WATCHLIST.md`/`us-stocks/WATCHLIST.md`'s methodology: chart
reads, staged entries, real capital, real trades. The two run in
parallel and shouldn't be conflated — TITA's paper-trading equity and
this account's real $50 are entirely separate, and a discretionary read
here says nothing about TITA's own signal on the same coin.

**Naming note, 2026-09-11**: the PSE/US-stocks discretionary methodology
this file ports got named **TITO** (TITA's sibling — see
`pse/WATCHLIST.md`'s header for the story). This file runs the same
TITO methodology on crypto, for whatever that's worth given how much
of it (catalyst categories, volume-screen source) needed adapting —
see the notes below.

## Working relationship: Crypto Research Analyst

Same mandate and boundaries as [`pse/WATCHLIST.md`](../pse/WATCHLIST.md)
and [`us-stocks/WATCHLIST.md`](../us-stocks/WATCHLIST.md): discretionary
technical analysis support — chart reading, staged entry/stop/target
construction, live price tracking. Not a systematic/backtested strategy.
Analyst, not directive-giver: entry/stop/target plus reasoning, decision
stays with the user (Portfolio Manager). No capital at risk on this end.

**What's genuinely different here, established 2026-09-11 when this
project started** (see the conversation that led to this file for the
full reasoning):
- **No earnings/dividends** — crypto catalysts are listings, protocol
  upgrades, funding rates, on-chain flow, regulatory news. The
  "catalyst" research step needs this different lens, not a port of the
  PSE/US earnings-check habit.
- **No market close** — 24/7 trading means the "screen after close,
  confirm next day" cadence doesn't map cleanly. Treat "close" framing
  in ported language as informal, not a real session boundary.
- **The volume-screen source is unproven.** PSE's screen used
  MarketScreener (stocks-only, doesn't cover crypto); US-stocks' uses
  stockmarketwatch.com's most-active page. Neither transfers. The
  working default is CoinMarketCap's top-by-market-cap or
  trending/gainers list — but CoinMarketCap's gainers list skews toward
  low-liquidity/pump-and-dump names (see the BE/ION-style caution
  applied to Bloom Energy and Ionics earlier in this project) more than
  PSE/US's most-active lists do. Extra skepticism warranted on anything
  screened this way, more than on a fresh PSE/US name.
- **Fractional trading is native, not a broker feature to verify.**
  Unlike Webull's stock-fractional-share gap (no automated stop-loss on
  fractional positions), crypto exchanges let you buy/sell any decimal
  amount by design — there's no "whole coin" concept the way there's a
  whole share. This removes an entire category of risk that dominated
  the US-stocks project's broker research. OKX's own help center
  confirms stop-loss (and OCO take-profit+stop-loss) orders are
  supported for spot trading — the Webull-style automated-stop-loss gap
  is not expected here, but **not yet confirmed in-app** the way the
  Webull gap was — verify on your first real position.

**Standing behaviors** (same as PSE/US): never trust a source's own
summary — direct-fetch and cross-check. Caveat every screen result as
provisional until chart-confirmed. Report losers as honestly as
winners.

## Broker & capital — OKX, $50 USD, status as of 2026-09-11

**Confirmed 2026-09-11**: the user will trade real capital, **$50 USD**,
on **OKX**.

**Fees** (WebSearch-sourced, not yet confirmed on OKX's own logged-in fee
page — verify against your actual "Assets → My trading fees" screen):
base/regular tier commonly cited as **0.08% maker / 0.10% taker** on
spot trades, dropping at higher 30-day volume or with OKB held. At $50
of capital this is a minor drag in isolation (a $15 trade costs ~1.5
cents each way at these rates) but matters if position sizes get pushed
very small relative to the per-pair minimum below.

**❗ Minimum trade size — the real constraint at this account size, per
a 2023 OKX announcement (directionally useful, may be stale — verify
live for any specific pair before trading it):** OKX enforces a
per-pair minimum spot order size that varies enormously — as low as 0.1
USDT (AAVE, AVAX) up to 10 USDT (ADA, ALGO, XLM, DAI, EOS, MANA) and far
higher on illiquid pairs (100-10,000+ USDT, effectively untradeable at
this account size). **This is the single most important thing to check
before adding any new coin to this watchlist** — a coin with a 10 USDT
minimum eats 20% of the account in one "minimum" position, which may
force an all-or-nothing sizing decision incompatible with the
starter+confirmation-add staged-entry methodology below. Prefer coins
with confirmed low minimums (BTC/ETH's own minimums are typically small,
~3 USDT per an earlier search) unless a genuinely strong setup justifies
checking a specific pair's current minimum first.

**Not yet tested**: whether OKX supports fractional-amount limit orders
cleanly at this size (expected yes, unlike Webull's stock-specific
gap, but not yet confirmed with a real fill the way NVDA/INTC's Webull
fills confirmed limit-order support there).

## Entry methodology: staged, not all-or-nothing

Same as [PSE](../pse/WATCHLIST.md#entry-methodology-staged-not-all-or-nothing)/
[US stocks](../us-stocks/WATCHLIST.md): **Starter** (smaller size, on
first touch into the stated entry zone, stop active immediately) +
**Confirmation add** (the remainder, on the first real stabilization
signal). At $50 total capital, size the Starter small enough that the
per-pair minimum trade size (see above) doesn't force an oversized
first tranche relative to the plan.

## Exit methodology: full profit-take, trader not investor

Same unified rule as PSE/US stocks (confirmed 2026-09-10 for those two
projects, applied here from the start): **take full profit at T1, exit
completely, look for the next entry.** No partial-hold, no long-term
framing — every entry here is a short-term trade by default.

## Portfolio Risk Rules

Same two standing rules as PSE/US stocks:
1. **Max single-position concentration: flag anything over 25-30% of
   total current portfolio value.** At $50 total capital this is a low
   bar in dollar terms (~$12.50-15) — worth checking whenever a fill is
   logged, same as always, but doesn't mean much until there's more
   than one or two positions open at once.
2. **Every new position gets a stop in the same update it's confirmed
   filled, no exceptions** — verify the stop order actually placed
   given OKX's spot stop-order support is not yet confirmed in-app.

## Daily workflow (standing process)

1. **Trigger: typing "cx_volume"** means fetch a current top-movers/
   top-market-cap list from CoinMarketCap (prefix `cx_` to stay
   distinct from PSE's bare triggers and US-stocks' `us_` triggers in
   the same conversation). Treat gainers with real caution per the note
   above — CoinMarketCap's trending list skews toward low-liquidity
   pump risk more than PSE/US's most-active lists do.
2. **Screen new names** via **investing.com's crypto technical-analysis
   pages** — confirmed working 2026-09-11 (tested BTC/ETH/SOL):
   `investing.com/crypto/{coin-name}/{ticker}-usd-technical` (e.g.
   `investing.com/crypto/bitcoin/btc-usd-technical`) gives Simple +
   Exponential MA5/10/20/50/100/200 (each tagged Buy/Sell) and RSI14
   with an overall Buy/Sell/Neutral summary — MarketScreener's
   PSE-only role, filled by a different source here. **One real gap**:
   only RSI14 is shown, not RSI9 like the PSE screen used — work with
   RSI14 alone unless a second source turns up. Same screening bar as
   PSE/US: flag names above their MAs with RSI not yet extended as
   "worth a closer look," still fully provisional until chart-confirmed.
3. **User pastes daily + weekly TradingView charts** (MACD + ATR added)
   for names worth a closer look — TradingView covers crypto pairs the
   same way it covers PSE/NASDAQ tickers, so this step ports directly,
   unlike step 1-2.
4. **Full chart-based verdict** — add with a staged entry if it holds
   up, or log under "Reviewed but NOT added" with the reason.
5. **Catalyst check, crypto-specific categories**: listings/delistings,
   protocol upgrades, funding-rate extremes, on-chain flow (exchange
   inflows/outflows, whale activity), regulatory news. Not earnings —
   see the note at the top of this file.
6. **Whenever a trade resolves**, log it in
   [`TRADE_JOURNAL.md`](TRADE_JOURNAL.md).

**Trigger: typing "cx_positions"** — live prices for Current Holdings.
**Trigger: typing "cx_summary"** — live prices for the Summary table.
**Trigger: typing "cx_catalyst"** — refresh catalysts for all names.

## Summary table

*(Empty — no names screened yet. Paste a chart or run `cx_volume` to
start.)*

## Current Holdings (already owned — not staged entries)

*(Empty — no real positions yet.)*

## Reviewed but NOT added (for reference — not maintained further)

*(Empty so far.)*
