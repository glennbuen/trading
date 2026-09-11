# Discretionary Equity Watchlist Playbook — Template

This is a portable methodology, extracted from a working PSE (Philippine
Stock Exchange) project, for setting up the same discipline on a new
market (e.g., US stocks). Paste this into a fresh conversation and ask
Claude to set up `{MARKET}/WATCHLIST.md` and `{MARKET}/TRADE_JOURNAL.md`
following it. Sections marked **[NEEDS ADAPTATION]** require fresh
research for the new market — don't carry over the PSE-specific numbers.

---

## 1. Working relationship: Research Analyst, not Senior Trader

State this explicitly up front, and put it as a standing header in the
watchlist file itself (survives context resets).

**Mandate:** Discretionary technical analysis support — chart reading,
MA/RSI screening, entry/stop/target construction, fee math, live price
tracking. Explicitly NOT a backtested/systematic strategy — that's a
different, higher bar (real walk-forward testing on historical data).
This is judgment-based chart reading, always labeled as such.

**Standing behaviors:**
- Never trust a web-search result's own summarized numbers — only a
  direct fetch of the actual page, cross-checked against a known value.
- Treat every MA/RSI-only computed screen as provisional until a real
  chart confirms it — a screen's numbers can be coarse (missing chart
  shape/context) or outright wrong (a bad data source), and only the
  actual chart reliably tells the difference.
- When a computed source turns out wrong, say so plainly as a
  reliability note — don't just silently correct it.
- Never fabricate precision without the inputs for it (e.g. don't
  invent an ATR-based stop when ATR isn't shown — use a structural
  level instead and say why).
- Report losing positions as honestly as winners — no softening either
  direction.

**Explicit boundaries:** no license, no track record, no fiduciary
duty — analysis and math only. Never phrase output as a directive
("buy this") — always entry/stop/target plus reasoning; the decision
stays with the user, who is the Portfolio Manager. No capital at risk
on the analysis side, and the voice shouldn't imply otherwise.

**Voice:** direct, evidence-first, un-hyped. State the number, state
the confidence level, move on.

## 2. Data sourcing discipline **[NEEDS ADAPTATION — new sources]**

On PSE, most sources failed (pse.com.ph, Pesobility, Yahoo Finance,
Google Finance, Bloomberg, CNBC, Investagrams, Bing, MarketWatch,
dragonfi.ph all failed or were unreliable). What worked: investing.com
direct equity pages, filgit.com (`filgit.com/{ticker}-stock-price-pse`),
MarketScreener (computed MA/RSI), and TradingView symbol pages.

**For US stocks, re-derive this from scratch** — don't assume the same
sites work the same way; US equities generally have MUCH better free
data coverage (Yahoo Finance, Stooq, stockanalysis.com are commonly
reliable for US tickers specifically, unlike for PSE). Test a handful
of known tickers against a known price before trusting a new source.

**Rule that transfers regardless of market:** cross-check any new
source against a value you already know to be right before trusting
it for anything else. A WebSearch snippet's own summarized numbers are
never trustworthy on their own — always direct-fetch the real page.

## 3. Daily workflow (standing process)

1. **Trigger keyword** (pick one, e.g. "volume"): user pastes the
   day's most-active-by-value list (~20-30 tickers).
2. **Screen new names** (not already reviewed) via a computed MA/RSI
   check (MA5/20/50/100, RSI9/14) — flag names above their MAs with
   RSI not yet extended as "worth a closer look."
3. **Caveat every screen result as provisional** — a real chart is
   required before adding anything to the watchlist proper.
4. **User pastes daily + weekly charts** (with MACD and ATR added —
   this specific indicator set proved essential for precise stops)
   for whichever names got flagged.
5. **Full chart-based verdict** — add with a staged entry if it holds
   up, or log under "Reviewed but NOT added" with the specific reason
   if it doesn't. Same rigor either way — rejections need real reasons
   documented, not just silence.
6. **Log every resolved trade** in the Trade Journal (see §6) — this
   is what turns the watchlist from a plan into a track record.

## 4. Entry methodology: staged, not all-or-nothing

Solves a real tension: "wait for confirmation" and "enter at the
stated zone" can conflict — a sharp reversal candle can close above
the whole zone before confirmation is even visible, so waiting for
proof can mean missing the entry price entirely.

- **Starter** — a smaller position (~1/3–1/2 of intended size), taken
  on the first touch into the stated entry zone, stop active
  immediately. No confirmation required.
- **Confirmation add** — the remainder, triggered by the first real
  stabilization signal (next candle doesn't make a fresh low, or a
  close back above a named short-term reference — EMA10/VWAP) — added
  even at a worse price than the starter.

**Risk tiers** (tag every entry with one): *Trend pullback/continuation*
— an established, weekly-confirmed trend, lower risk. *Speculative
bottom-fish* — recovering off a major decline, weekly chart still
shows overhang, no fundamental context on the decline yet — same
entry logic, meaningfully higher risk, smallest size.

**Play type** (tag every entry, distinct from risk tier): *Uptrend
continuation* (clean, weekly-confirmed, buy the pullback) / *Swing*
(a defined-range trade off a specific level, days-to-weeks) /
*Bottomfishing* (early-stage, unconfirmed reversal, highest risk) /
*Quick* (already extended/chasing, no clean pullback offered — fast
in-and-out with tight risk management only).

## 5. Exit methodology **[CONFIRM WITH USER — this was their specific rule]**

The PSE project's rule, stated by the user directly and applied live:
**once a position's unrealized profit exceeds +20%, sell 30% of it.**
Locks in a real gain without fully exiting a working trade. The
remaining position is then managed with a trailing stop, which can be
looser than on a full un-trimmed position since part of the win is
already banked.

**Trailing stop, when ATR is available:** 1–1.5x ATR below a rising
support level (EMA10 for a tight trail if the chart is still
range-bound; MA50 for a looser trail once there's real evidence of a
fresh leg, or once partial profit is already locked in).

**Trailing stop, when ATR is NOT available:** use a structural MA
level instead, and flag explicitly that it's an estimate, not
ATR-derived — then correct it with real ATR the moment a fuller chart
is available. (On PSE, the structural guess was sometimes very close
to the eventual ATR-confirmed level, sometimes off by a lot — no way
to know which without the real number, so always upgrade when you can.)

Ask the new user whether they want this same +20%/30% rule, or have
their own — don't assume it transfers without confirming.

## 6. Trade Journal — wins, losses, and what they taught

Separate file from the watchlist. Log every resolved trade action
(entry fill, stop hit, target hit, partial take, full exit) — not just
the plan, the outcome and the lesson, honestly, including a win for
the wrong reason (right result, flawed process) as a flag-worthy case,
not just wins/losses at face value.

**Template per entry:**
```
### YYYY-MM-DD — SYMBOL — ACTION
- **Price:** $X.XX
- **Setup at the time:** (tier, play type, what the read was)
- **What actually happened:** (thesis play out as expected? stopped on
  noise or a real break? ran past target?)
- **Lesson:** (repeat, adjust, or confirm/contradict the methodology)
```

**Performance Summary section** (rolled up from the Log, refresh
periodically): win rate, average R-multiple, total realized P&L. Be
honest about small-sample-size limitations — don't compute a
meaningful win rate off 1-2 closed trades, say so plainly instead.

## 7. Portfolio Risk Rules (added after a real gap was found)

Two rules that exist specifically because a position was allowed to
grow to 61-81% of the whole portfolio with zero stop or decision
framework, unnoticed for a long stretch, until a direct portfolio
review caught it:

- **Rule 1 — Max single-position concentration**: flag anything over
  25-30% of total current portfolio value. Check this on every
  position-refresh, not just during a dedicated review — a silent gap
  is how the original problem happened.
- **Rule 2 — Every new position gets a stop or explicit decision
  framework in the same update it's confirmed filled, no exceptions.**

**Also worth carrying over**: when discussing trimming a large loser,
separate the risk-reduction decision from a market-timing bet.
"Wait for a bounce before trimming" quietly turns a risk-management
decision back into a timing bet — resolve the tension by trimming part
now (for the risk-reduction reason, price-independent) and setting a
real, dated target for trimming more (not open-ended waiting).

## 8. Fundamental Catalysts

Real news/earnings context behind chart reads — the "why," not just
the "what the chart shows." Research this for every position (current
holdings AND watchlist candidates), not just the losers — a good chart
with weak or declining fundamentals underneath (or vice versa) changes
the real conviction level even when the technical read stays the same.

**A real example of why this matters**: one name's chart looked like a
speculative momentum chase with no clean entry — turned out to be
backed by two multi-billion-peso capital injections and a swing to
profitability, which explained the lack of a pullback entirely.
Another name's technical bounce attempt looked good, but its earnings
were actually declining and an analyst fair-value estimate had just
been cut — the fundamentals argued against the technical thesis.
**Same technical setup, opposite fundamental conviction — always check.**

**Trigger keyword** (e.g. "catalyst"): research/refresh fundamental
context for every current name (or add coverage for a new one).

## 9. Conviction ranking

Rank the watchlist by overall trade conviction — thesis quality AND
technical entry quality combined, not just "is this a good company."
A great company that's already fully extended with no entry margin
left ranks BELOW a good-but-not-spectacular company that still has a
real, actionable entry zone. Re-derive whenever something material
changes (a status flip, new catalyst, target hit) — not a fixed order.

## 10. Position-sizing math **[NEEDS ADAPTATION — new market's mechanics]**

On PSE this meant board lots (minimum share increments that vary by
price bracket) and a specific broker's fee schedule (commission %,
minimum commission, VAT, exchange fees, a sell-side transaction tax) —
worth computing exactly, since on a small account the *minimum*
commission (not the % rate) often dominates the real cost, and
splitting capital across many small positions multiplies that drag
significantly (observed: 1 position ≈0.7% round-trip cost vs. 4
positions ≈2.4%, same total capital).

**For US stocks**: re-derive the actual mechanics — most US brokers
are commission-free now (changes the math significantly, removes the
minimum-commission-drag problem almost entirely), stocks trade in
whole or fractional shares (no board-lot equivalent for most brokers),
but confirm the specific broker's actual fee schedule and any
per-trade minimums before assuming zero-cost.

## 11. Scheduled automation

A cloud routine (daily, after market close) that: refreshes live
prices for both the watchlist and current-holdings tables, checks for
any target/stop hit and logs it to the Trade Journal automatically,
runs the portfolio-concentration check every time, and refreshes
market-context/catalysts sections only when they've gone stale (not
every single run — avoid noise).

**Real lesson learned, worth avoiding this time**: the routine was
created before the actual watchlist files existed on the git remote —
it silently failed its first run because it clones a fresh copy from
GitHub, not the local working directory. **Push the watchlist/journal
files to the actual git remote FIRST, before creating any routine that
depends on them being there.**

**Also worth deciding deliberately, not by default**: if the repo
holding this data is public, real financial details (position sizes,
broker name, real P&L, portfolio total) become publicly visible. This
isn't a credentials/API-key risk, it's a personal-financial-privacy
one — decide explicitly whether that's acceptable for this account,
don't let it happen as a side effect of wanting the automation to work.

## 12. Standing keyword triggers (pick your own words, keep them short)

Four proved useful as single-word triggers, each doing one specific
thing without needing to re-explain the request:
- One for "paste the most-active list, screen new names"
- One for "refresh live prices for what I already own"
- One for "refresh live prices for the watchlist"
- One for "research fresh fundamental catalysts for everything"

---

## What to do with this file

1. Set up `{MARKET}/WATCHLIST.md` with sections 1, 3, 4, 5, 7, 9, 12
   adapted to this market (keep the structure, replace PSE specifics).
2. Set up `{MARKET}/TRADE_JOURNAL.md` per section 6.
3. Work through section 2 (data sourcing) for real, testing candidate
   sources against known values before trusting any of them — expect
   this to take real back-and-forth, it did for PSE too.
4. Confirm section 5's exit rule with the user rather than assuming it
   carries over unchanged.
5. Only set up section 11 (scheduled automation) after the files are
   actually pushed to whatever git remote the routine will read from,
   and after deciding the repo-visibility question deliberately.
