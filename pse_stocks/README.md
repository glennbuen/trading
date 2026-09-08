# pse_stocks/

Philippine Stock Exchange (PSE) equities work — kept separate from
`cryptobot/` and `daytrading/`, which are both OKX crypto, built on a
data pipeline (`cryptobot.data`) that only talks to OKX via ccxt. There
is no PSE equivalent wired into this project — no live feed, no
screener, no historical OHLCV fetcher. Nothing in `cryptobot/` or
`daytrading/` can be pointed at a PSE ticker as-is.

## Status

Discretionary chart reads only so far — no systematic strategy,
backtest, or data pipeline built for PSE names yet. Two names read to
date, straight off pasted TradingView screenshots (not from any data
this project fetched itself):

- **BPI** (Bank of the Philippine Islands), 1D, ~Sep 2026: sitting
  almost exactly at its 150/200MA cluster (~₱105.4) after a rally off a
  June low (~₱92), both longer MAs still sloping down. Read: not a
  confirmed entry at that price — sitting in an unresolved resistance
  test, not through it. Two more objective alternatives given: wait for
  a clean daily close above the recent ~₱108-109 high (breakout
  confirmation), or wait for a pullback to MA50 (~₱103.3)/MA20 for a
  bounce entry. Next earnings ~November per the chart's quarterly
  cadence, not an immediate factor.
- **IMI** (Integrated Micro-Electronics), 1D, ~Sep 2026: up ~140% in
  under 3 months (₱3.50 → ₱8.40), including a +13% single-day move on
  the day read, price 90%+ above its 200MA, RSI(14) 73.97 (overbought).
  Read: a parabolic, extended move — the opposite situation from BPI
  (already stretched, not at a decision point). Close to the SPYFRAT
  Parabolic Framework's own "sell on sight" territory (`cryptobot/
  engines/parabolic_risk.py`'s `is_ephr`, RSI(30) daily+weekly >80),
  though the exact classification wasn't run (no weekly RSI(30) data
  for IMI). Chasing here read as high mean-reversion risk, especially
  with a quarterly earnings report likely coming up in the next couple
  months while the stock is this extended.

## The indicator setup being read (matches the user's own TradingView layout)

- MA 150, MA 200 (the long-term trend / major resistance-support
  reference)
- MA 50 (medium-term trend)
- MA 20, EMA 10 (short-term / pullback-entry reference)
- RSI(14)
- Volume (20-period)
- TradingView's own earnings ("E") and dividend ("D") calendar markers
  — informational only, not a trading signal; relevant mainly for
  flagging upcoming event risk (an earnings date near an already-
  extended stock) rather than reading anything into past marker
  placement itself.

## The real data gap, and the plan

Going through PSE stocks by volume (e.g. "≥30M shares") the way this
project has gone through OKX symbols requires a working PSE data
source — a real OHLCV history plus a live/most-active screener.
`pse.com.ph`'s own "Most Active" page renders its data client-side
(nothing usable came back on a plain fetch); other aggregators tried
during this session either blocked the request (403) or, when fetched
anyway, returned numbers that visibly contradicted each other between
sources — unreliable enough that they were not used.

**User's plan: build the actual PSE data pipeline in n8n, as a separate
project from this one.** Likely approach discussed: find the JSON
endpoint the PSE site's own frontend JS calls to populate its most-
active table (browser DevTools → Network → XHR/Fetch), and have n8n
call that directly on a schedule; fall back to a headless-browser node
(Puppeteer/Playwright/Browserless) if no clean API turns up. Output
would land somewhere this project (or a future PSE-specific one) can
read from — a sheet, a database, a webhook.

## Once real PSE data exists

The honest next step, matching how `cryptobot/` itself was built: a
`pse_stocks/data/` provider mirroring `cryptobot/data/`'s own shape (a
thin data-source wrapper + the same canonical OHLCV schema —
`ts, dt, open, high, low, close, volume`), then real engines and
strategies on top of it, tested with the same no-lookahead discipline
and honest walk-forward evaluation used throughout this project — not
before. Until then, PSE work in this project stays what it's been:
manual, one chart at a time, discretionary, and explicitly not
backtested.
