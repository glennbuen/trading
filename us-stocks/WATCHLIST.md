# US Stocks Chart Watchlist — Near-Entry Setups Only

**Strategy name: TITO** (same one used in `pse/WATCHLIST.md` — TITA's
discretionary sibling, named 2026-09-11. See that file's header for
the naming story). Trend-aligned mean reversion — buy a pullback to
the MA within an established uptrend, staged entry (Starter +
Confirmation-add), ATR-based stops, full exit at T1. One methodology,
used across both `pse/` and `us-stocks/`.

## Working relationship: US Equities Research Analyst

**Mandate:** Discretionary technical analysis support for US-listed
stocks — chart reading, MA/RSI screening, entry/stop/target
construction, live price tracking. Not a systematic/backtested
strategy (that standard belongs to `cryptobot/`'s TITA in this same
repo — TITO is its discretionary sibling, not the same kind of thing);
this is judgment-based chart reading, always labeled as such. Ported
from the PSE project (`pse/WATCHLIST.md`, `pse/PLAYBOOK_TEMPLATE.md`)
— same discipline, new market.

**Standing behaviors:**
- Never trust a WebSearch snippet's own summary — only a direct fetch,
  cross-checked against a known value.
- Treat every MA/RSI-only screen as provisional until a real chart
  confirms it.
- When a computed source turns out wrong, say so plainly as a
  reliability note, not just fix it silently.
- Never fabricate precision without the inputs for it — e.g. don't
  invent an ATR-based stop when ATR isn't shown; use a structural
  level instead and say why.
- Report losers as honestly as winners — no softening either direction.

**Explicit boundaries:** no license, no track record, no fiduciary
duty — analysis and math only. Never phrase output as a directive
("buy this") — always entry/stop/target plus reasoning; the decision
stays with the user, who is the Portfolio Manager. No capital at risk
on this end, voice shouldn't imply otherwise.

**Voice:** Direct, evidence-first, un-hyped. State the number, state
the confidence level, move on.

## Note on data sourcing (tested 2026-09-10 against AAPL)

Much better starting position than the PSE project, where most sources
failed. For a large-cap US ticker (AAPL), **five sources agreed
precisely** on the same price/change/range: investing.com
(`investing.com/equities/{slug}`), TradingView symbol pages
(`tradingview.com/symbols/{EXCHANGE}-{TICKER}/`), stockanalysis.com
(`stockanalysis.com/stocks/{TICKER}/`), MarketScreener (also gives
computed MA5/20/50/100 + RSI9/14), and **even Yahoo Finance worked**
(it 503'd for every PSE ticker tried — that was evidently a PSE-side
gap, not a Yahoo-wide one).

**Most-active list**: `stockanalysis.com/markets/active/` works, but
— same caveat as PSE — it's ranked by **share volume**, not dollar
value, so it's dominated by sub-$1 penny stocks. Worth finding a
dollar-value-ranked version before relying on it heavily; not yet done.

**Still to verify**: whether this multi-source agreement holds for
mid/small-cap and low-liquidity US names too, or whether (like PSE)
reliability drops off outside the most liquid, well-covered tickers.
Don't assume AAPL-level agreement generalizes — test before trusting
a source on anything less liquid.

## Daily workflow (standing process)

1. **Trigger: typing "us_volume"** means fetch the day's most-active
   list directly via WebFetch from
   `https://stockmarketwatch.com/screen/most-active` (confirmed working
   2026-09-11 — no need to wait for the user to paste a screenshot or
   the URL). Treat the fetched list as the input to step 2
   automatically. (Prefixed `us_` deliberately, to stay distinct from
   the PSE project's bare "volume"/"positions"/"summary"/"catalyst"
   triggers in the same conversation context — PSE's "volume" still
   requires a pasted list/screenshot, since no working autonomous
   source was found for that market; this asymmetry is intentional,
   not an inconsistency to fix.)
2. **Screen new names** (not already reviewed) via MarketScreener
   MA5/20/50/100 + RSI9/14 — flag names above their MAs with RSI not
   yet extended as "worth a closer look."
3. **Caveat every screen result as provisional** until chart-confirmed
   — never add to the watchlist proper off the screen alone.
4. **User pastes daily + weekly charts** (MACD + ATR added — this
   indicator set proved essential for precise stops on PSE) for
   flagged names.
5. **Catalyst check, every name, before the verdict — scoped to this
   account's T1-only exit rule, not a full deep-dive.** Two specific
   questions, not the PSE-style multi-year thesis: (a) is there a
   near-term *dated* event (earnings, FDA, macro release) that could
   land before T1 is likely reached — this is the bigger risk for a
   fast trade, not less, since there's less time buffer to react; (b)
   is the current move backed by real news, or could it reverse on a
   dime with no fundamental follow-through? Skip the long-term
   thesis/multi-year growth story/12-month price targets — not
   relevant to a trade that exits at T1. Do this whether the chart
   looks like an add or a reject.
6. **Full chart + catalyst verdict** — add with a staged entry if it
   holds up, or log under "Reviewed but NOT added" with the specific
   reason, catalyst included either way.
7. **Log every resolved trade** in `TRADE_JOURNAL.md`.

## Entry methodology: staged, not all-or-nothing

Same reasoning as PSE: "wait for confirmation" and "enter at the
stated zone" can conflict — a sharp reversal candle can close above
the whole zone before confirmation is visible.

- **Starter** — a smaller position (~1/3–1/2 of intended size), taken
  on the first touch into the stated entry zone, stop active
  immediately. No confirmation required.
- **Confirmation add** — the remainder, triggered by the first real
  stabilization signal (next candle no fresh low, or a close back
  above a named short-term reference — EMA10/VWAP), added even at a
  worse price.

**Risk tiers**: *Trend pullback/continuation* (established,
weekly-confirmed trend, lower risk) vs. *Speculative bottom-fish*
(recovering off a major decline, weekly overhang still present,
smallest size, highest risk).

**Play type**: *Uptrend continuation* / *Swing* / *Bottomfishing* /
*Quick* (already extended/chasing, no clean pullback — fast in-and-out
only, regardless of how good the underlying trend looks).

## Exit methodology — CONFIRMED 2026-09-10: full profit-take, rotate fast

Deliberately different from PSE's rule (sell 30% at +20%, trail the
rest) — this account's objective is capital velocity, not maximizing
any single trade's upside. **Take full profit at T1 (~8-15% gain),
exit completely, redeploy once the sale settles.**

**Why not "quick gains" via chasing extended setups**: that would mean
systematically picking the worst risk/reward entries (no margin of
safety) to try to trade faster. The actual lever for speed is faster
*exits* on properly-entered (real pullback/confirmation) setups, not
looser entries.

**The GFV constraint sets the real cadence**: US settlement is T+1 —
sell today, funds settle tomorrow. "Redeploy once settled" means
realistically **next business day at the earliest**, not a same-day
flip, unless there's enough separately-settled cash sitting idle to
fund the next entry without touching yesterday's proceeds. See
"Broker & capital" above — flag explicitly whenever a sell and a
same-day/next-day new buy are both being considered.

**Stop-loss discipline stays as tight as PSE's, if not tighter** — a
blown account compounds at 0% forever, and fast-turnover trading on a
small account is exactly the style most prone to overtrading. Growth
speed only matters if the account survives to keep compounding.

**Trailing stop, when ATR is available**: 1–1.5x ATR below a rising
support level. Less central to this account's style than PSE's (full
exits at T1 are the default, not a trail-and-hold), but still the
right tool if a position runs well past T1 and holding longer makes
sense for a specific setup.
**When ATR is NOT available**: structural MA level, explicitly flagged
as an estimate, upgraded to ATR-based the moment a fuller chart is
available.

## Portfolio Risk Rules (carried over from PSE, applies from day one)

- **Rule 1 — Max single-position concentration**: flag anything over
  25-30% of total current portfolio value, checked on every
  position-refresh, not just during a dedicated review.
- **Rule 2 — Every new position gets a stop or explicit decision
  framework in the same update it's confirmed filled, no exceptions.**

## Broker & capital ($78.77 USD starting capital, converted from S$100) — status as of 2026-09-11

**Corrected 2026-09-11**: starting capital is **$78.77 USD**, not $100
— the account was funded with S$100 and converted at ~0.79, confirmed
exactly by real fill math (see Current Holdings above). Earlier
sections below still say "$100" in places — treat $78.77 as the real
number; the board-lot/GFV/fee mechanics discussed don't change, only
the total.

**Broker decision is OPEN again — the earlier switch to Moomoo was
based on a real research error, now corrected.** History, kept for
context on how this conclusion was reached (a live example of this
project's own "correct errors transparently" discipline):

1. First pass conflated Webull US mechanics with Webull Singapore
   (a separate, MAS-licensed entity — Webull Securities (Singapore)
   Pte Ltd) and concluded Webull only supports market orders on
   fractional shares. **That claim came from a source about "Webull
   Financial LLC" clearing via "Apex Clearing Corporation" — the US
   entity, not Singapore's.**
2. Switched the decision to Moomoo on that (mistaken) basis, since
   Moomoo confirmed limit-order support for fractional shares.
3. **Direct fetch of Webull SG's own FAQ (webull.com.sg/help/faq/1230)
   corrected this**: Webull Singapore's official instructions
   explicitly walk through BOTH order types — "4a. Select Order Type:
   MARKET..." and "4b. Select Order Type: LIMIT... trade in fractional
   share amount up to 5 decimal places." **Webull SG does support
   limit orders on fractional shares.** (One loose thread: a Webull
   API doc referenced market-orders-only at a technical level — likely
   outdated or US-specific too; the direct SG consumer FAQ is trusted
   over that.)

**Net result: the two brokers are closer than the sequence of
corrections above suggested, and Webull may be the better pick.**

| | Webull SG | Moomoo SG |
|---|---|---|
| Commission | $0 (confirmed) | $0, lifetime (confirmed) |
| Platform fee | $0 (confirmed, unexplained "T&Cs apply" asterisk not resolved) | $0 for new clients' first 12 months, then ~$0.99/order |
| Fractional order types | Market **and** Limit (confirmed directly, corrected from earlier error) | Market and Limit (confirmed) |
| Fractional-eligible stocks | **✅ All 7 confirmed by user 2026-09-10** — INTC, TSM, NVDA, META, AMD, NBIS, MRVL all show the green-diamond fractional flag on Webull SG | Not checked (moot now) |
| Stop-loss on fractional positions | Unconfirmed | Unconfirmed |
| GFV / PDT rules | Same US rules apply either way — see below | Same |

**✅ DECISION 2026-09-10 (final): Webull Singapore is the confirmed
broker.** All three real blockers are now resolved in Webull's favor:
genuinely cheaper (confirmed $0 commission + $0 platform fee), same
limit-order capability on fractional shares as Moomoo (the earlier
"market-only" claim was a research error, corrected), and all 7
watchlist names confirmed fractional-eligible. **One loose thread
remains, not a blocker**: the unexplained "T&Cs apply" asterisk on
Webull's $0 fee claim — worth understanding before a real trade, but
not a reason to prefer Moomoo given everything else favors Webull.
**❌ CONFIRMED 2026-09-11 (user tested in-app): Webull SG does NOT
allow automated stop-loss orders on fractional shares.** This is the
real answer to the open question above, and it's the worse case — not
just "untested," genuinely unsupported. Since both live positions
(NVDA, INTC) are fractional-sized by necessity given the $78.77
budget, **there is currently no automated stop-loss safety net on
either position** — a breach has to be caught and acted on manually.

**Practical mitigation, given this constraint is likely permanent for
this account's position sizes:**
1. **Set price alerts instead** (a notification, not an executable
   order) at each stop level if Webull supports alerts on fractional
   holdings — check this specifically, since alerts are usually a
   lighter-weight feature than stop orders and may not carry the same
   restriction.
2. **Increase manual check frequency** via "us_positions" specifically
   when a position is trading anywhere near its stop level — don't
   rely on the routine daily cadence alone if a name is under real
   pressure (like INTC's -5.57% day).
3. **Whole-share positions may not have this restriction** — worth
   testing once a position is sized large enough to buy at least 1
   full share of a cheaper name, since the fractional restriction is
   specifically about fractional order types, not Webull's stop-loss
   feature generally.
4. Consider extending the scheduled daily routine (see PSE's version)
   to this project too, specifically to flag if any Current Holdings
   position has breached its stop level — it can't execute the sell,
   but it can catch and alert on a breach between manual checks.

**SEC/FINRA regulatory fees** (apply on US stock sells regardless of
broker): $27.80 per $1M sold (SEC, $0.01 min), $0.000166/share (FINRA
TAF, capped $8.30, $0.01 min) — negligible at this account size either
way.

**Real risk specific to this account type: Good Faith Violations.** At
$100 this will be a cash account (not margin) — exempt from the
Pattern Day Trader rule (margin-only), but subject to GFVs instead: US
settlement is **T+1** (sell Monday, funds settle Tuesday), and reusing
unsettled sale proceeds to open a new position before settlement
triggers a violation. **3 GFVs in 12 months restricts the account to
settled cash only, 4 triggers a 90-day restriction, 5 closes the
account.**

**Standing rule for this project**: after any sell (stop-out, target
hit, partial take), treat that cash as unavailable for a new buy until
the next business day, not just "available since it shows in the
account." Flag this explicitly whenever a sell and a same-day
redeploy are both being considered.

## Summary table

**Trigger: typing "us_summary"** means pull fresh live current prices
for every symbol below and re-render this table.

| Rank | Symbol | Tier | Play type | Recommended | Catalyst | Entry range | Stop-loss | Take-profit (T1) | Current price | Status | What confirms the add |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **INTC** | Trend reversal/continuation | Swing | Short-term (T1 exit) | Strongest catalyst reviewed so far — multiple concrete confirmed events, not sentiment: **US government holds a 10% stake**; Nvidia investing $5B to co-develop custom x86 CPUs + $8.9B government investment; **Apple reportedly designing/building chips with Intel in the US** (stock +8-11% on this news); 18A-P process entering risk production on time; $20B+ raise saw $100B in institutional demand. Next earnings Oct 22 — ~6 weeks out, outside T1 horizon. | $100–106 (this week's low to current — a live test of weekly MA20 at 107.36) | ~$91–94 (1–1.5x daily ATR 5.38 below MA50 99.62) | ~$115–120 (~9-15% off entry) | $102.94 (+2.61% today) | ✅ **Starter FILLED overnight 2026-09-10/11** — 0.15 fractional sh @ $101.6173 ($15.24). Bouncing back after yesterday's -5.57% reversal, now modestly above cost basis again. Now also in Current Holdings above; stop (~$91-94) still clear. | Weekly close above 107.36 (MA20), or daily close above EMA10 |
| 2 | **AMZN** | Trend pullback/continuation (no weekly overhang at all) | Swing | Short-term (T1 exit) | Real, ongoing growth story, not just a good chart: Q3 2026 guidance $197-202B revenue (+9-12% YoY), operating income guided to $22.5-26.5B (up sharply from $17.4B a year ago); consensus "Strong Buy" (49 of 57 analysts), average target $327.38 (~27% upside), Street-high $405. Ongoing layoffs framed as an AI-focus cost discipline story, not distress. An FTC ad-pricing lawsuit dinged the stock Sept 1 but it has since recovered past that level. Next earnings ~Oct 22-29 — 6+ weeks out, outside T1 horizon. | $255–259 (daily MA50/EMA10/VWAP cluster AND weekly MA20 — both timeframes converge almost exactly here, essentially live now) | ~$246–249 (1–1.5x daily ATR 6.27 below the zone) | ~$283–287 (52w-high retest, ~3.3:1 R:R off entry/stop) | $256.78 (unchanged — **data quality note**: no confirmed fresh Sept 12 print yet, multiple sources still show the Sept 11 close; treat as stale until a new tick confirms) | 🟢 **Live now** (as of last confirmed price) — sitting almost exactly on its own daily+weekly confluence zone | Next daily candle no fresh low vs. today (253.14), or close remains above EMA10 (256.59) |
| 3 | **MSFT** | Trend pullback/continuation (no weekly overhang, weekly RSI 61.14 not extended) | Swing | Short-term (T1 exit) | Genuinely fresh, substantive: Azure growth hit 43% with annualized revenue above $100B, backlog surged 84% to $678B, and Microsoft just started disclosing Azure revenue separately for the first time (a real transparency/credibility signal). Analysts raised the target to $600 from $500 on this. Real background risk, not acute: ~$50B+ quarterly capex and a revised ~$175B 2026 CapEx outlook has investors debating AI-spend ROI — the same debate as AMZN's. Stock is up only +4.26% YTD despite this — "gone nowhere in 2026" per one headline, which is itself part of the case (real strength not yet fully re-rated). Next earnings ~Oct 27-28 — 6+ weeks out, outside T1 horizon. | $492–497 (daily MA20/EMA10/VWAP cluster — essentially live now, matches today's range 492.58–498.97) | ~$477–482 (1–1.5x daily ATR 10.66 below the zone) | ~$540–554 (52w-high retest 553.72, ~3.6:1 R:R off entry/stop) | $495.63 (unchanged — **data quality note**: same issue as AMZN, no confirmed fresh Sept 12 print; one source showed a $494.82 after-hours tick from Sept 11, -0.16%, still not a new session) | 🟢 **Live now** (as of last confirmed price) — sitting right on the daily confluence zone, though the weekly hasn't pulled back nearly as much toward its own nearer averages (EMA10 470.66, MA20 434.17) — this is a daily-level pause inside a stronger uptrend, not as clean a multi-timeframe convergence as AMZN's | Next daily candle no fresh low vs. today (492.58), or close holds above EMA10 (496.41) |
| 4 | **TSM** | Trend pullback/continuation | Swing | Short-term (T1 exit) | Extremely strong, consistent (not one-quarter) growth: Aug revenue +53.3% YoY, Q2 2026 revenue +36%/net income +77.4% YoY, Q3 guidance $44.6-45.8B rev at 65-67% gross margin. AI chip demand outstripping supply. Next earnings ~mid-October, moderate distance out. | $420–425 (daily MA50/MA20/EMA10 cluster, current price only ~2.5-3.5% above — close to live) | ~$403–409 (1–1.5x daily ATR 11.49 below zone) | ~$460–475 (~9-13% off entry, approaching 52w high 479.00) | $433.24 (+1.22% today — first genuinely fresh Sept 12 print, resolves the earlier data-quality issue) | ⏳ Moved further from the zone — now ~2% above $420-425 rather than within ~1% | Next daily candle no fresh low, or close back above EMA10 (425.10, now stale — worth a fresh chart) |
| 5 | **NVDA** | Trend pullback/continuation (cleanest yet) | Swing | Short-term (T1 exit) | No near-term earnings risk (next report Nov 17/25 — 2+ months out). DOJ probing Nvidia's $20B Groq licensing deal for antitrust concerns — real but a known, ongoing story since December, background risk not a fresh acute catalyst. | $220.80–223.67 (MA20/EMA10/current cluster — may already be live) | ~$210–213 (1–1.5x daily ATR 7.15 below MA20, under MA50 211.80) | ~$236–240 (52w-high retest, ~6-8% off entry) | $218.29 (~flat today) | ✅ **Starter FILLED overnight 2026-09-10/11** — 0.07 fractional sh @ $218.41 ($15.29), *below* the stated zone. Essentially flat to cost basis, holding steady. Now also in Current Holdings above; stop (~$210-213) still clear. | Next daily candle no fresh low, or close back above EMA10 (223.16, now stale — worth a fresh chart) |
| 6 | **META** | Trend pullback/continuation | Swing | Short-term (T1 exit) | JPMorgan upgraded to Overweight ($640→$820 target) on real AI product traction (Muse AI agent #3 in App Store) + capex guidance well above consensus. Also reached an **$18B settlement with 29 states** today over Instagram/Facebook youth-harm claims — a real legal overhang getting resolved (de-risking, not just noise), adding to today's move. Next earnings Oct 28 — well outside a T1-only holding period, low near-term event risk. | $598–610 (MA50/EMA10 cluster) | ~$566–577 (1–1.5x daily ATR 21.49 below zone) | ~$680–700 (~12-16% off entry, T1-only target per this account's exit rule) | $648.03 (+0.57% today — resumed climbing after yesterday's pullback) | ⏳ Still well above the $598-610 zone, no pullback opportunity yet | Next daily candle no fresh low vs. the pullback low, or a close back above EMA10 (603.87, now stale — worth a fresh chart) |
| 7 | **AMD** | Trend pullback/continuation | Swing | Short-term (T1 exit) | CFO claims addressable market could reach $3 trillion; data-center revenue projected to hit $70B by 2027; new Helios rack-scale AI platform shipping (announced at IFA conference). Real, specific company news, not just riding Nvidia's coattails. Next earnings Nov 3 — 8 weeks out, low near-term risk. | $479–490 (daily EMA10/MA20 cluster) | ~$444–456 (1–1.5x daily ATR 23.23 below zone) | ~$555–570 (~8-15% off entry, near 52w high 584.73) | $516.13 (+2.80% today — gave back yesterday's pullback, moving further from the zone again) | ⏳ Now ~5-7% above the $479-490 zone | Next daily candle no fresh low vs. the pullback low, or a close back above EMA10 (483.82, now stale — worth a fresh chart) |
| 8 | **NBIS** | Trend pullback/continuation | Swing | Short-term (T1 exit) | Fresh, credible catalyst (2 days old): Palantir named Nebius its preferred sovereign AI infrastructure partner (Sept 8, 2026) — a specific enterprise deal, not vague sentiment. Next earnings likely early-mid Nov (based on Q3 2025's Nov 11 pattern) — outside T1 horizon. | $223.70–228.90 (daily EMA10/MA20 cluster) | ~$196–205 (1–1.5x daily ATR 18.53 below zone) | ~$250–255 (near-term prior high retest, ~10-13% off entry) | $224.55 (-1.56% today) | 🟢 **Still IN the stated entry zone ($223.70–228.90), now near its lower end** — second straight down day, the pullback thesis continues to hold up | Next daily candle no fresh low vs. today confirms the add — a fresh chart would help given two days of movement inside the zone |
| 9 | **MRVL** | Trend pullback/continuation | Swing | Short-term (T1 exit) | Real, ongoing growth story: revenue targets raised to $12B (FY2027) and $18B (FY2028) on AI chip demand, positioning as "the Switzerland of AI" (diversified customer base), real Amazon chips deal boosting shares. **AI Infra Summit Sept 15-17 — a near-term date to watch** (product showcase, not earnings risk). Last earnings Aug 28 already reported; next likely ~3 months out. | $223–227 (daily MA20/EMA10 cluster) | ~$200–208 (1–1.5x daily ATR 15.44 below zone) | ~$245–255 (near-term high retest, ~9-13% off entry) | $236.10 (+3.26% today, reportedly $237.93 intraday after an investor-lunch AI discussion) | ❌ **Back OUT of the zone** — yesterday's dip into $223-227 didn't hold; a real one-day pullback, not a confirmed add | Would need another pullback into $223-227, then a no-fresh-low candle |

## Current Holdings (already owned — not staged entries)

**Trigger: typing "us_positions"** means pull live current prices for
every symbol in this table and report each against cost basis,
unrealized %, and trailing-stop level on file.

**Capital tracking (real, 2026-09-10 night fills)**: starting capital
was S$100, converted to **$78.77 USD** (not the $100 USD assumed
elsewhere in this file until now — corrected 2026-09-11 once real
fills confirmed the conversion). Deployed: NVDA $15.29 + INTC $15.24 =
**$30.53**. Cash remaining: **$48.24** (user-confirmed, reconciles
exactly: $78.77 − $30.53 = $48.24).

| Symbol | Cost basis (real) | Current price | Unrealized | Stop-loss (initial, per Portfolio Risk Rule 2) | Exit plan | Technical read |
|---|---|---|---|---|---|---|
| **NVDA** | $218.41 (0.07 fractional sh, $15.29) | $218.36 (-2.37% today) | -0.02% | ~$210–213 (no automated stop — Webull SG doesn't support one on fractional shares, see Broker & capital) | Full exit at T1 ~$236–240 per this account's T1-exit rule | Filled *below* the stated zone ($220.80–223.67) — a better entry than planned. Essentially flat now after today's pullback — stop is well clear. |
| **INTC** | $101.6173 (0.15 fractional sh, $15.24) | $100.32 (-5.57% today) | -1.28% | ~$91–94 (no automated stop — same fractional-share gap) | Full exit at T1 ~$115–120 per this account's T1-exit rule | Filled inside the stated zone ($100–106). **-5.57% single-day move** — still above the stop zone, not close to breaching, but a real move worth understanding (a foundry-spinoff/IPO-exploration headline surfaced earlier and was never fully dug into — worth revisiting if you want the detail). |

## Fundamental Catalysts

**Trigger: typing "us_catalyst"** means research fresh news/earnings
for every name in Current Holdings and the Summary table (or add
coverage for a name not yet listed) — update this section, the
Catalyst columns in both tables, and re-derive the conviction ranking
if anything material changed.

**Standing rule, added after a real gap was caught 2026-09-10 (MU's
first review skipped it): every single-name review gets a catalyst
check, not just names that get added.** A rejection logged without
researching *why* the stock actually moved is an incomplete review —
MU's rejection read very differently once the real catalyst (a
genuine AI-memory earnings supercycle, not speculative froth) was
factored in, even though the technical verdict didn't change. Do this
before finishing any review, added or rejected, not as a follow-up
only when asked.

**AMZN** (added 2026-09-11): Q3 2026 guidance is real and strong —
$197-202B revenue guided (+9-12% YoY), operating income guided
$22.5-26.5B vs. $17.4B a year ago. Consensus "Strong Buy" (49 of 57
analysts), average target $327.38 (~27% above current price), Street-
high $405. Ongoing layoffs are being framed as a deliberate AI-capex
reallocation (~$220B planned for 2026 against ~$775.7B trailing
revenue), not a distress signal — worth some skepticism on the ROI
debate that framing invites, but not a reason to read the layoffs as
bearish on their own. An FTC lawsuit over ad pricing knocked the stock
down to $259.77 on Sept 1 — real legal risk, not fully resolved, but
the stock has already traded back above that level, so it isn't
currently the dominant story. Next earnings ~Oct 22-29 (sources
disagree by about a week) — either way, outside a T1-only holding
window.

**MSFT** (added 2026-09-11): Genuinely fresh, not a rehash of the old
"AI capex" story — Azure growth hit 43% with annualized revenue above
$100B, backlog surged 84% to $678B, and Microsoft began disclosing
Azure revenue as its own line item for the first time (a real
transparency signal, not just a marketing claim). Analysts responded
by raising the target to $600 from $500. Real background risk, same
flavor as AMZN's: $50B+ quarterly capex and a revised ~$175B 2026
CapEx outlook have investors debating AI-spend ROI — a genuine, live
concern, not dismissed here. Notably the stock is up only +4.26% YTD
despite all this — one headline framed it as "gone nowhere in 2026,"
which cuts both ways: either the market isn't buying the Azure story
yet, or the re-rating hasn't happened yet and this is the
underappreciated setup. Next earnings ~Oct 27-28 — 6+ weeks out,
outside T1 horizon.

*(Populate further as names are added. Same practice as PSE: research
real news/earnings for every position AND watchlist candidate, not
just the losers — a good chart with weak fundamentals underneath, or
vice versa, changes real conviction even when the technical read
stays the same.)*

## Reviewed but NOT added (for reference — not maintained further)

- **BE (Bloom Energy)** (2026-09-11, $258.49 MarketScreener close /
  $267.90 stockmarketwatch intraday) — **RSI-overbought + stacked
  near-term event risk, not an extension-magnitude reject like MU/LITE.**
  Above every meaningful MA (MA20 $224.77, MA50 $226.87, MA100 $251.44)
  but RSI9 = **72.94**, RSI14 = 65.43 — fails the screen's own
  not-yet-extended bar, same reason ION got excluded on the PSE side
  the same day. Ran from $206 (Aug 31) to $252.87 (Sep 4) — ~23% in
  days — then further to today's price, on real news: **S&P 500
  inclusion effective Monday, September 21** (UBS raised target to
  $325, Clear Street to $330), the actual driver of the move. This is
  exactly the "near-term dated event that could land before T1" risk
  this project flags for a T1-only trade — index-inclusion runs often
  see a sell-the-news effect once funds finish front-running the
  actual date. Stacked on top: a **securities class-action lawsuit
  deadline September 28** — already caused a real -3.5% single-day
  drop when investors first weighed the legal notice. Underlying
  fundamentals are genuinely strong (Q2 revenue +166% YoY to $1.065B,
  $20B backlog, AI data-center demand) — not a hollow move, but that
  doesn't change the entry-timing math. Worth revisiting only if it
  gives back a meaningful chunk of the move and RSI resets.

- **MU (Micron Technology)** (2026-09-10, $1,027.77) — **extreme
  extension risk, a different category from a standard reject.** Daily
  chart alone looks like a normal pullback-and-reclaim (above every
  daily MA, RSI 60.6 moderate). Weekly MA200 is $207.07 — price is
  currently **~5x (396%) above its own 4-year weekly average**, even
  after a real ~30-35% correction already happened (peak ~$1,200 in
  Jul, low ~$800, now recovering). 52-week range $131.56–$1,255 —
  roughly a 9x move in under two years. Unlike a FGEN-style single-
  session gap (an easy reject), this move shows genuine time and
  structure — which makes it more tempting, not less, but the sheer
  **magnitude** means even a pullback to the daily MA20/50 cluster
  would still leave price ~55% above the weekly MA200 — a standard
  stop-loss doesn't meaningfully protect against a real air-pocket at
  this scale. Rejected on extension magnitude, not chart shape.
  **Catalyst (researched after the user flagged this review was
  missing one): genuinely real, not speculative froth.** Q3 FY2026
  revenue $41.46B (+74% YoY), gross margin 84.9%, EPS $25.11 (+13x
  YoY) — a massive beat. Riding a real AI-memory supercycle: 24% DRAM
  / 15% NAND market share, HBM demand structurally supply-constrained
  "well beyond calendar 2026," $100B in customer commitments already
  booked. **Specific dated catalyst ahead: Q4 FY2026 earnings Sept 30**,
  consensus expecting ~$50.8B revenue (+350% YoY) — an extraordinarily
  high bar that cuts both ways: a beat could extend the run, but
  merely-good-not-extraordinary results against expectations that
  lofty is exactly the setup for a sharp sell-the-news reversal,
  independent of whether the business itself stays strong. **Revised
  framing: not speculative like FGEN, a genuinely great business — but
  "good company" and "good entry point right now" are different
  questions, and the extension math doesn't change regardless of how
  real the fundamentals are.** Worth revisiting on a deeper pullback,
  or specifically around the Sept 30 print for the volatility it'll
  bring either direction — not a standard entry today.

- **MSTR (Strategy Inc)** (2026-09-10, $132.70) — **active breakdown,
  not a pullback.** Weekly price below both weekly MA200 ($162.60,
  -18.4%) and MA50 ($158.31) — only above the short-term MA20/EMA10.
  Chart shows a classic boom-bust pattern: a massive parabolic spike
  to ~$400 (2025) followed by a ~65-70% crash, with only a recent,
  tentative stabilization attempt. Today's action is that attempt
  failing, not a buy signal — daily candle opened near the high
  ($141.82), closed near the low ($132.70), -2.80% daily / -7.07%
  weekly, closing at/near lows on both timeframes simultaneously.
  **Catalyst: confirmed this is Bitcoin-driven, not company-specific.**
  MSTR holds ~845,050 BTC (avg cost ~$75,412/coin) and is "the largest
  listed bitcoin treasury on earth" — stock performance tracks
  Bitcoin's price directly, not operating earnings. Even bullish
  analysts are trimming: Bernstein cut its target from $450 to $350
  while keeping Outperform — a real signal of growing caution, not
  just noise. Trading this would effectively be a short-term Bitcoin
  bet, a different risk category from the other names reviewed today.
  Rejected on both chart (active breakdown) and catalyst (confirmed
  the decline is real, not an overreaction).

- **ORCL (Oracle Corp)** (2026-09-10, $161.63) — **rejected, and not
  just technically.** Weekly chart shows a real crash pattern, not a
  pullback: price spiked to a 52-week high of $345.72, then fell
  **~53%** to current levels — above weekly MA200 (+8% only) but
  **below weekly MA50** (-11.3%). Daily price is even below daily
  MA200 ($168.18) despite sitting above the shorter MA20/50/EMA10 — a
  recent bounce within still-damaged longer-term structure, the same
  shape as MSTR's boom-bust, not INTC/TSM/NVDA's genuine trend-pullback
  character. **Critical catalyst finding: Oracle's earnings were TODAY
  (2026-09-10), and the reaction is already negative** — the company
  announced another **$40B in debt/equity**, capex +162% to $55.7B,
  and **-$23.7B in free cash flow**, reportedly sending shares down
  **10% after-hours**. This explains the whole pattern: a genuinely
  massive AI/cloud backlog ($638B, OCI +93%) drove the original spike,
  and growing market alarm about the debt/capex/FCF burden needed to
  fund it explains the crash since — today's fresh raise just added to
  it. **Rejected doubly: the chart alone doesn't qualify, and today's
  earnings reaction means any entry zone drawn from this chart is
  about to be stale — a real risk of the stock gapping through a stop
  at tomorrow's open.** Textbook case for why the near-term-event
  check in this account's workflow exists.

- **SPCX (SpaceX Exploration Technologies Corp)** (2026-09-10, $147.55)
  — **rejected for a different reason than any other name today: an
  active, recurring unlock overhang, not weak fundamentals or a bad
  chart shape.** IPO'd June 11-12, 2026 (largest IPO in history, priced
  $135, closed first day $161 +19.3%) — only ~3 months of trading
  history, which is why MA200 and weekly RSI/MACD/ATR are all blank on
  this chart; there isn't enough history yet to evaluate a real trend.
  **A staggered insider lockup unlock schedule has a tranche landing
  right around today (Sept 10, ~7% of eligible shares)** — almost
  certainly connected to today's real -3.86% decline. More unlocks
  continue through the full lockup expiration on **Dec 8, 2026**
  (Musk's 6.4B shares stay locked until June 2027) — an ongoing,
  recurring supply-overhang risk, not a one-time event already priced
  in. **Fundamentals are genuinely excellent**: Q2 2026 revenue +92%
  YoY (~$4.1B→~$7.9B) — this isn't a bad-company rejection. Next
  earnings Nov 5. Worth revisiting once the staggered unlocks conclude
  or settle into a predictable pattern — not a fit for a quick T1
  trade right now given the recurring event risk.

- **LITE (Lumentum Holdings)** (2026-09-10, $988.98) — **extreme
  extension risk, same category as MU, not a standard reject.** Weekly
  MA200 is $202.43 — price is **~389% above its own 4-year weekly
  average**, nearly matching MU's 396%, the most extended chart
  reviewed apart from MU itself. This week's candle alone is +12.22%;
  years of relative flatness (2021-2024) followed by a near-vertical
  parabolic move starting 2025-2026. 52-week range $144.52–$1,085.68 —
  roughly a 7.5x move in a year. **Catalyst is genuinely real, same
  story as MU**: 140% YTD rally driven by real AI-optical
  infrastructure demand, Deutsche Bank initiated Buy coverage Aug 31,
  FY2026 revenue guidance raised ($2.92B→$2.98B) and EPS estimate
  raised ($4.45→$5.00) — not speculative froth. **Rejected on the same
  grounds as MU: a great business doesn't change the extension math.**
  Applying the discipline consistently rather than making an exception
  because the story sounds good — the air-pocket risk at this
  magnitude exists independent of fundamental quality.
