# PSE Chart Watchlist — Near-Entry Setups Only

## Working relationship: PSE Research Analyst

**Mandate:** Discretionary technical analysis support for PSE stocks —
chart reading, MA/RSI screening, entry/stop/target construction, fee
and board-lot math, live price tracking. Not a systematic/backtested
strategy (that standard belongs to `cryptobot/`'s TITA); this is
judgment-based chart reading, always labeled as such.

**Standing behaviors:**
- Never trust a WebSearch snippet's own summary — only a direct fetch,
  cross-checked against a known value.
- Treat every MA/RSI-only screen as provisional until a real chart
  confirms it (FGEN, DMC, and SGP were all corrected this way).
- When a computed source turns out wrong (DMC's MarketScreener numbers
  contradicted the real chart), say so plainly and flag it as a
  reliability note, not just fix it silently.
- Never fabricate precision without the inputs for it — e.g. don't
  invent an ATR-based stop when ATR isn't shown on the chart; use a
  structural level instead and say why.
- Report losers as honestly as winners — no softening either direction
  (SCC at -52% gets the same rigor as LTG at +33%).

**Explicit boundaries:** no license, no track record, no fiduciary
duty — analysis and math only. Never phrase output as a directive
("buy this") — always entry/stop/target plus reasoning; the decision
stays with the user, who is the Portfolio Manager here. No capital at
risk on this end, and the voice shouldn't imply otherwise.

**Voice:** Direct, evidence-first, un-hyped — no "huge upside!"
language, no false confidence, but not hedged into uselessness either.
State the number, state the confidence level, move on.

## Daily workflow (standing process)

1. **Trigger: typing "volume"** means the user is about to paste the
   day's most-active-by-volume/value list (~20-30 stocks — e.g. a
   Pesobility screenshot, or the filgit.com homepage table — see "Note
   on live-price sourcing" below). Treat the pasted list as the input
   to step 2 below automatically, no need to ask what to do with it.
2. **Screen new names** (not already reviewed in this file) via
   MarketScreener MA5/20/50/100 + RSI9/14 for a quick potential read —
   flag names above their MAs with RSI not yet extended as "worth a
   closer look," same bar used throughout this session.
3. **Caveat every screen result as provisional**, per this session's
   own lessons: MA/RSI numbers alone can't distinguish a healthy
   sustained uptrend (ICT, OGP) from a parabolic gap (FGEN) or an
   outright-wrong computed number (DMC) — never add a name to the
   watchlist proper off the screen alone.
4. **User pastes daily + weekly TradingView charts** (with MACD and
   ATR added, the now-standard indicator set) for whichever names got
   flagged as worth a closer look.
5. **Full chart-based verdict** — add to the watchlist with a staged
   entry (per the Entry methodology below) if it holds up, or log it
   under "Reviewed but NOT added" with the specific reason if it
   doesn't, same rigor either way.
6. **Whenever a trade actually resolves** (entry fills, stop hit,
   target hit, partial take, full exit) — log it in
   [`TRADE_JOURNAL.md`](TRADE_JOURNAL.md): what happened, and the
   lesson, win or loss alike. This is what turns the watchlist from a
   plan into a track record.

## Market context: PSEi (updated 2026-09-09)

Corrects an earlier "PSE is a bear market" framing that hadn't been
checked against the index itself. **Not a deep bear market** — PSEi
fell from a 2024-25 peak (~7400+) to a 52w low of 5584.35 and has been
recovering since. **But it is in a genuine near-term corrective phase**:
a sharp daily-chart decline from the August high (~6400+) down to
current **6105.99**, RSI soft on both timeframes (48.83 weekly, 44.88
daily — below midline, not oversold), and — this is the load-bearing
fact — **price is sitting almost exactly on weekly MA50 (6105.89) right
now**, a live index-level support test. Weekly MA200 (6422.68) is the
bigger level above, ~5% away.

**Why this matters for every entry below:** several individual names on
this list (BPI, BLOOM) are testing their own MA50/weekly-support levels
at the same time the index itself is testing its. If the index holds
6105-6106 and bounces, that's a tailwind for the pullback entries on
this list. If it breaks down toward weekly MA200's ~5% gap instead,
that's a headwind that would pressure even the cleanest individual
setups (NIKL, Philweb) regardless of their own chart quality. Re-check
this section against a fresh PSEi chart periodically — it's not a
one-time read.

**Note on sourcing:** the user only posts charts already screened as
looking like they have upside potential — "reviewed but not added"
below reflects charts they posted that *my* read disagreed with (no
clear trend/setup), not something they filtered out beforehand.

**Note on live-price sourcing:** of the many sources tried for
autonomous PSE data (pse.com.ph, Pesobility, Yahoo Finance, Google
Finance, Bloomberg, CNBC, Investagrams, Bing, MarketWatch, TradingView's
"most active" markets page, dragonfi.ph — all failed, blocked, or
returned unreliable/mismatched data), four work:
- **investing.com** (direct equity quote pages) — reliable current
  price/OHLC, but historical-data view caps at ~1 month.
- **filgit.com** (`filgit.com/{ticker}-stock-price-pse`) — reliable live
  intraday quote + period rollups (5D/1M/3M/6M/YTD/1Y highs/lows), same
  ~1-month-equivalent depth, no daily history table.
- **TradingView symbol pages** (`tradingview.com/symbols/PSE-{ticker}/`)
  — different URL pattern from the markets page that failed; gives
  last price, all-time high/low with dates (useful cross-check — APX's
  ATH of 18.46 independently confirmed the T2 level below), and 1D/1W/
  1M/YTD/1Y % performance, but no OHLC day-range or MA/RSI/MACD values
  in the fetched content.
- **MarketScreener** (`marketscreener.com/quote/stock/{SLUG}-{ID}/quotes/`
  — find the right SLUG-ID via WebSearch first, matching ticker AND
  "Philippines S.E." explicitly since some names have duplicate OTC
  listings) — **the most valuable of the four**: gives price, day
  range, previous close, AND **computed MA5/20/50/100 + RSI9/14
  directly** — no need to derive indicators from raw history. Cross-
  checked tightly against the original chart reads: APX's RSI14
  (61.64) matched the chart read to the decimal; NIKL's MA50 (3.933 vs.
  chart's 3.93) and Philweb's MA20 (14.26 vs. 14.26) essentially
  matched too. Still no MA150/200, but this meaningfully raises the
  ceiling on analyzing PSE names that haven't been chart-reviewed —
  RSI/MA20/MA50/MA100 confluence reads are now possible, not just
  RSI/MACD/ATR/EMA10.

All four cross-validate closely against each other on current price
(e.g. Sep 10 AM: BLOOM 2.27 filgit/MarketScreener vs. 2.26 TradingView,
NIKL 4.76 filgit/MarketScreener vs. 4.78 TradingView — normal snapshot-
timing noise, not disagreement).

## PSE trading hours (for scheduling checks)

**9:00 AM – 3:00 PM, Monday–Friday, Philippine time.** (Web sources
disagreed with each other on this — one said 3:15pm close, another
3:00pm with a run-off, a general prior assumption said 3:30pm — this is
the user-confirmed correct version, use it over anything conflicting
found online.) Two useful checkpoints given this: **~2:30 PM** for a
preview scan of the most-active list (what's approaching a zone, get
ready) and **after 3:00 PM** for actually evaluating confirmation
triggers below, since those are defined off the settled daily close,
not a pre-close snapshot.

## Entry methodology: staged, not all-or-nothing

Added after a real problem got flagged: "wait for confirmation" and
"enter at the stated zone" can genuinely conflict — if confirmation
turns out to be a sharp reversal candle, it can close *above* the whole
entry zone, and by the time it's visible the good price is already
gone. Full confirmation and the best price are often mutually
exclusive; picking one extreme (chase confirmation, or buy blind) isn't
the answer. Every entry below now uses two tranches instead of one:

- **Starter** — a smaller position (~1/3–1/2 of intended size), taken
  on the first touch into the stated entry zone, stop active
  immediately at the listed level. No confirmation required — this
  piece exists so a sharp bounce doesn't leave you with zero exposure.
- **Confirmation add** — the remainder, triggered by the first real
  stabilization signal (the next candle doesn't make a fresh low vs.
  the prior one, or a close back above the nearest short-term
  reference — EMA10/VWAP, specified per name below) — added even if
  that's at a somewhat worse price than the starter.

If price never dips into the zone and just runs, the starter is what
you have; if it dips and confirms cleanly, both tranches fill close
together. Either way there's no scenario where waiting for proof means
walking away with nothing.

## Exit methodology — SUPERSEDED 2026-09-10: full profit-take, trader not investor

**The user has revised the strategy for this account too**: adopt the
same approach built for `us-stocks/` (see that file's Exit methodology
and `us-stocks-exit-rule` memory) — **take full profit at T1, exit
completely, look for the next entry.** No partial-hold, no long-term
"Both"/investor framing. Explicit shift from "trader + occasional
long-term hold" to **trader only**.

**What this changes for names already tagged "long-term candidate"**
(NIKL, ICT, OGP, APX, DMC currently carry "Both" or long-term language
in the Recommended column and their detailed entries) — that framing
is now deprioritized. Treat every entry as a short-term trade exiting
at T1 by default; the long-term-fundamentals notes stay in the file as
useful context (still real information) but no longer drive how a
position is actually managed.

**Resolved 2026-09-10 — LTG is grandfathered under the old rule.** The
user's explicit call: keep LTG's remaining 70% on its existing trail
(₱14.29–14.52, weekly ATR-based), not forced into a full exit under
the new rule. The new T1-full-exit approach applies going forward to
new decisions — and once it's proven out in practice, the plan is to
use it to trim other positions too (SCC being the obvious next
candidate given the still-open concentration/trim decision there).
LTG itself isn't being retroactively unwound.

**Old rule, kept for reference / historical context only** (what
governed the BPI/BLOOM Starters and LTG's partial take up to this
point): once unrealized profit exceeded +20%, sell 30%, trail the
remainder with a structural or ATR-based stop. Not the active rule
going forward — superseded by the above.

## Portfolio Risk Rules (standing policy, added 2026-09-10)

Added after SCC was found to have grown to 61.4% of current portfolio
value (81% by cost basis) with zero stop or decision framework, months
into the position, before anyone caught it. These two rules exist so
that gap doesn't recur with a different name.

**Rule 1 — Max single-position concentration: flag anything over 25-30%
of total current portfolio value.** Check this whenever "positions" is
run, or whenever a new fill is logged — if a position (existing or
newly filled) pushes past this threshold, say so explicitly in that
response, don't wait for a dedicated portfolio review to notice.
**Currently at the line**: two names, as of the 2026-09-11 NIKL buy —
**SCC** (~28.1% of portfolio value, post-trim, down from 61.4%; still
the largest position, still no technical stop on the remaining 800
shares, still an open auction-risk thesis) and **LTG** (~26.8% — newly
in the flag band simply from price appreciation, not new buying,
worth noting but not an action item on its own). NIKL's new Starter
(~9.2%) and BPI/BLOOM (~4-5% each) are not a concentration concern.

**Rule 2 — Every new position gets a stop or explicit decision
framework in the same update it's confirmed filled, no exceptions.**
BPI and BLOOM's Starters both got initial stops (₱101.00–101.50,
₱2.05–2.10) immediately per this rule, already good practice — this
formalizes it as a standing requirement rather than something that
happened to occur, so a future fast-moving fill doesn't slip through
without one the way SCC evidently did originally.

## Summary table

**Trigger: typing "summary"** means pull fresh live current prices for
every symbol below (the stocks-to-buy list) and re-render this table —
distinct from "positions," which is for the Current Holdings table
(already-owned) above, not this one. **Added 2026-09-11: also flag,
explicitly and every time, which names would benefit from a fresh
daily/weekly chart paste** — the MA/EMA/stop/target levels in this
table are static snapshots from whenever each name was last
chart-reviewed (per its "Reviewed:" date in the detail entry below),
they don't move just because price does. Flag a name if any of:
- **Price has drifted >~5-7% from the level the last chart read was
  based on** (e.g., APX's stop/trail was explicitly called "a rough
  estimate pending a fresh ATR chart" after its pullback off the highs)
- **A stated stop/trail is already marked stale or approximate** in the
  file's own language, not just computed from current price
- **Price is testing or has crossed a key level** from the last chart
  (an MA, the stated entry/stop/target zone) where a fresh read would
  sharpen or change the call — DMC sitting right at weekly MA20 is the
  live example
- **Several sessions have passed since the "Reviewed:" date** with no
  fresh chart, regardless of whether price moved much

Say this plainly in the summary response ("worth a fresh chart on X, Y"
or "nothing needs a refresh right now") — don't wait to be asked, and
don't bury it if the answer is "nothing," say that explicitly too.
**Specify which timeframe(s) — daily, weekly, or both — not just "a
fresh chart."** Reason it out per name: a stale ATR/trailing-stop or a
fast-moving daily structure calls for daily; a confirmation trigger
defined on the weekly (like a weekly MA close) calls for weekly;
flag both only when both are genuinely stale, not by default.

**Last price update: 2026-09-11, 3:00 PM PH close — live quotes from
filgit.com (see Note on sourcing).** All entries staged (starter on touch +
confirmation add on stabilization) — see per-name detail below for the
exact confirmation trigger. "Entry range" is the zone both tranches
fill within. Stop-loss and take-profit are structural/ATR-based levels
set at review time — they don't move with the current price, only the
**Status** column does.

**Ranked by overall trade conviction** (thesis quality + technical
entry quality combined — not just "is this a good company"), 1
strongest. Re-assess this ranking whenever material new info comes in;
it's not a fixed order.

| Rank | Symbol | Tier | **Play type** | Horizon | **Recommended** | **Catalyst** | Entry range | Stop-loss | Take-profit | Current price | Status | What confirms the add |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **ICT** | Trend pullback (cleanest yet) | Uptrend continuation | Short-term + long-term candidate | Both | First PSE co. past ₱2T mkt cap; Mexico terminal expansion; "Strong Buy," 13 analysts, target ₱1,099 | ₱947–962 (pullback zone) | ₱900–915 (ATR-confirmed, corrected 2026-09-10 from ₱938–942) | T1 ₱1,000 · T2 (52w high) ₱1,049 | ₱985.00 (3:00 PM close, -0.20% today, range 980–988) | ⏳ Running further, hasn't pulled back into the zone yet | Hold in ₱947–962 zone confirmed by next candle not making a fresh low, OR reclaim of EMA10 (944.94) |
| 2 | **NIKL** | Trend pullback | Swing / Uptrend continuation | Short-term (T1 full-exit rule applies — see below) | Short-term | H1 2026 NI +93% YoY to ₱4.06B (Aug 7 report), EBITDA +67%; tight nickel supply/demand tailwind, analyst target ₱5.53 | ₱4.25–4.45 | ₱3.90–3.95 | T1 ₱5.20–5.40 (full exit here, not partial) | ₱4.54 (3:00 PM close, -5.02% today, range 4.52–4.75) | ✅ **Starter FILLED** (1,000 sh @ ₱4.6738 avg) — now a fourth straight red session since the fill, but still well clear of the stop | Next candle not making a fresh low vs. today confirms full conviction; deeper zone ₱4.25–4.45 was the confirmation-add trigger, moot now that the starter already filled in the shallow zone |
| 3 | **OGP** | Trend pullback | Uptrend continuation | Short-term + long-term candidate | Both | Didipio mine life extended to 2037; $1.958B long-term investment confirmed; solid 2026 production guidance | ₱34.20–36.65 | ₱32.60–33.15 (ATR-confirmed, close to original ₱33.50 guess) | T1 ₱40.00 · T2 (52w high) ₱40.50 | ₱38.60 (3:00 PM close, -1.03% today, range 37.80–38.60) | ⏳ Recovered off today's low, still above the entry zone and below T1 | Next candle no fresh low, OR close above EMA10 (36.90), if it keeps dropping into the ₱34.20–36.65 zone |
| 4 | **APX** | Trend pullback | Quick (was Uptrend — broke to new highs then pulling back) | Short-term + long-term candidate | Both | H1 2026 NI +68% YoY, Q1 EPS +92%; analyst target ₱22.00, above the new 52w high | ₱15.50–15.80 (deep) · ₱16.30–16.50 (shallow) | Trail (see detail below — old fixed stop ₱14.20–14.40 stale, trail level itself is a rough estimate pending a fresh ATR chart) | T1 ✅ hit · T2 ✅ hit · **T3 (new) ₱19.70–20.00**, trail don't hold | ₱18.16 (3:00 PM close, -0.22% today, range 17.62–18.18) | ✅ Recovered most of today's dip, well above the old fixed stop | N/A — already well past entry, managing the existing run |
| 5 | **Philweb (WEB)** | Trend pullback | Quick (momentum chase — never gave a pullback) | Short-term only | Short-term | Q2 swung to profit, rev +96%; ₱2.02B + ₱4.23B capital injections (Gokongwei, JKS stake) | ₱14.20–14.45 | ₱13.50–13.70 | ₱16.00–16.50 | ₱15.50 (3:00 PM close, -1.90% today, range 15.20–15.50) | ❌ Still above the ₱14.20–14.45 zone | Would need to keep falling into ₱14.20–14.45, then a no-fresh-low candle |
| 6 | **CNPF** | Trend pullback (weekly still unconfirmed) | Swing | Short-term (T1 full-exit rule applies) | Short-term | H1 2026 NI +6% YoY (₱4.14B), rev +15%; analyst "Strong Buy" (9), target ₱41.58 — but a month-old print, not fresh news behind today's move | ₱32.37–32.48 (EMA10/MA20 daily) | ₱31.00–31.20 (ATR-confirmed) | T1 ₱34.60–34.70 (weekly MA50/daily MA200 confluence, full exit) | ₱33.70 (3:00 PM close, +5.31% today, range 31.75–33.70) | 🆕 Added 2026-09-11 — closed at the day's high, the extended candle itself | Next candle not making a fresh low vs. today, if it dips into the ₱32.37–32.48 zone; weekly close above 33.62 (weekly MA200) would strengthen the read further |
| 7 | **BPI** | Trend pullback | Swing | Short-term | Short-term | Q1 miss vs forecast but +1.7% YoY NI; 2026 outlook targets high-single-digit growth | ₱102.50–104.00 | ₱101.00–101.50 | T1 ₱108–109 · T2 ₱114–115 | ₱103.10 (3:00 PM close, -0.96% today, range 102.60–104.00) | ✅ **Starter FILLED** (20 sh @ ₱103.6050 avg) — still inside the stated zone | Next daily candle makes no fresh low vs. prior day, OR close back above EMA10 (104.63)/VWAP (104.33) |
| 8 | **BLOOM** | Speculative bottom-fish | Bottomfishing | Short-term, smallest size | Short-term | Q2 loss narrowed sharply (₱1.41B→₱345M YoY), EBITDA +35%, GGR +15% | ₱2.17–2.32 | ₱2.05–2.10 | T1 ₱2.45 · T2 ₱2.60 | ₱2.23 (3:00 PM close, -0.45% today, range 2.20–2.30) | ✅ **Starter FILLED** (1,000 sh @ ₱2.2567 avg) — gave back today's earlier gain, now marginally underwater vs. cost | Next candle makes no fresh low, OR close back above ₱2.34 (EMA10) |
| 9 | **DMC** | Speculative bottom-fish | Bottomfishing | Short-term entry, long-term candidate on fundamentals | Short-term (long-term on fundamentals) | Softer: Q1 NI -2% YoY, FY25 NI -21%; fair value cut ₱10.04→9.42 — tempers the thesis | ₱7.86–8.02 | ₱7.57–7.67 (ATR-confirmed) | T1 ₱9.50–9.71 · T2 ₱10.65–11.00 | ₱8.14 (3:00 PM close, -0.97% today, range 8.10–8.22) | ⚠️ Slipped just under weekly MA20 (8.19) — daily EMA10 still reclaimed, but the weekly confirmation is no longer holding cleanly | Weekly close back above ₱8.19 (MA20) — daily EMA10 (7.87) already reclaimed, weekly now testing too |

**Conviction rank reasoning**: #1-3 (ICT, NIKL, OGP) — clean weekly-
confirmed trends with strong fundamental confirmation and, for
NIKL/OGP, an actual entry zone still available. #4-5 (APX, Philweb) —
excellent underlying theses, but both are fully extended right now
with no real entry margin left, so conviction in the company doesn't
translate to conviction in a fresh trade today. **#6 (CNPF, new
2026-09-11)** — strong fundamentals (real H1 earnings growth, "Strong
Buy" analyst consensus) rival the top tier, but the chart itself is
only now testing weekly MA200 with weekly MA50 still overhead — a
genuine reversal attempt, not yet the confirmed trend ICT/NIKL/OGP
have. Ranked below the fully-extended-but-proven APX/Philweb because
CNPF's own weekly structure isn't proven yet either, but above BPI
because the fundamental backing is meaningfully stronger. #7 (BPI) —
solid but technically and fundamentally the most "average" of the
trend-pullback names. #8-9 (BLOOM, DMC) — speculative tier by design;
BLOOM's fundamentals now support the bounce thesis, DMC's argue
against it.

**Play type key**: *Uptrend continuation* — clean, weekly-confirmed established trend, buy the pullback, can be held longer if it keeps working. *Swing* — a defined-range trade off a specific technical level, expect days-to-weeks not months. *Bottomfishing* — early-stage, unconfirmed reversal off a real low, smallest size, highest risk. *Quick* — the move is already extended/chasing, no clean pullback offered — treat as a fast in-and-out with tight risk management, not a multi-week hold expectation, regardless of how good the underlying trend looks.

Full reasoning, invalidation conditions, and the fundamental context
behind each horizon call are in the detailed entries below — this table
is a quick reference, not a replacement for reading the "why."
BLOOM's T1 R:R is weak on its own (~1.2:1) — that target mainly matters
as a checkpoint toward T2, not a target worth exiting fully at.

**On the two "ran without entering" names (Philweb, APX):** this is the
waiting-costs-you-the-entry scenario the staged-entry methodology was
built to soften, and it still happened to the starter-only piece here
because price never even touched the stated zones — there was no dip to
catch, staged or not. Nothing to do differently in hindsight; both are
now chase risk, not pullback entries, unless they give back the move.

## Fundamental Catalysts (researched 2026-09-10)

**Trigger: typing "catalyst"** means research fresh news/earnings for
every name currently in Current Holdings and the Summary table (or add
coverage for a name not yet listed here) — update this section, the
Catalyst columns in both tables, and re-derive the conviction ranking
if anything material changed. No need to ask what's wanted, this is
the standing request — same pattern as "volume"/"positions"/"summary."

Real news/earnings context behind the chart reads, prompted by the
user asking to research catalysts for every position and watchlist
name — this is the "why," not just the "what the chart shows." Not a
one-time check; worth re-pulling whenever a name's technical read
seems to have shifted meaningfully, since a chart can move well before
or after the news explaining it (Philweb is the clearest example here).

**Current Holdings:**
- **LTG**: Q2 2026 net income +24% YoY, revenue +6.3%, EPS ₱0.88 vs
  ₱0.71. Dividend ex-date just passed (Sep 7), 8.2% yield. Real
  earnings growth underneath the chart strength.
- **SCC**: see the full dedicated section under Current Holdings below
  — the coal-block auction/contract-expiry risk is the dominant story
  here, not routine earnings.
- **BLOOM**: Q2 2026 net loss narrowed sharply to ₱345.3M (from ₱1.41B
  a year ago), revenue +10.9% YoY, EBITDA +34.9% YoY, GGR +14.8%. A
  genuinely improving trend — supports the early-stage-recovery thesis
  better than the chart alone did.
- **BPI**: Q1 2026 slightly missed forecasts (EPS ₱3.20 vs ₱3.47) but
  still +1.7% YoY net income; 2026 outlook targets high-single-digit
  NI growth. Mixed but stable — the miss may partly explain the
  current pullback to MA50, not a breakdown.

**Watchlist candidates:**
- **NIKL** (refreshed 2026-09-11): the earlier "+312% YoY" figure was
  full-year 2025 — the more current print is **H1 2026 (Jan-Jun,
  published Aug 7, 2026): attributable net income +93% YoY to ₱4.06B,
  EBITDA +67% YoY to ₱8.68B**, driven by higher ore prices, +10% YoY
  shipment volumes, and a favorable peso-dollar rate ([Inquirer](https://business.inquirer.net/604365/nickel-asia-books-93-higher-h1-profit)).
  **Worth the nuance**: Q1 2026 standalone was actually weak (net
  income -26% YoY to ₱372M, [Manila Times](https://www.manilatimes.net/2026/05/13/business/nickel-asia-q1-income-slips-26-to-p372m/))
  despite higher ore prices at the time — meaning Q2 2026 alone carried
  the H1 strength, not a smooth trend across both quarters. Macro
  backdrop: nickel prices have stabilized in the $16,500-18,000/t range
  (Indonesian supply concerns, El Niño-related water constraints at
  Morowali Industrial Park providing a tailwind), but ING flags demand
  as still soft with no confirmed supply squeeze yet — a real but not
  runaway tailwind. Tight nickel supply/demand still the broad thesis;
  analyst target ₱5.53. **Not a new catalyst, for the record**: a
  Coral Bay Nickel/Sumitomo stake-sale story surfaces in searches but
  that deal was signed February 2025 — old news, not something
  explaining today's price action.
- **APX**: H1 2026 net income **+68%** YoY, Q1 EPS +92%. Analyst
  target ₱22.00 (above the already-new 52w high). Real earnings
  growth underneath the move, not just momentum.
- **CNPF** (new 2026-09-11): H1 2026 net income +6% YoY (₱4.14B vs
  ₱3.90B), revenue +15% YoY (₱45.8B), driven by double-digit growth in
  both branded and OEM-export businesses — published early August
  2026, a real and solid print. Analyst consensus "Strong Buy" (9
  analysts), 12-month target ₱41.58 (~23% above today's ₱33.70 —
  Simply Wall St's own page framed this as "58% upside," which is
  clearly calculated off a stale, much lower price, not today's; the
  ₱41.58 target itself looks like a genuine current figure, just not
  their upside-% framing of it). **Scoped catalyst check for today's
  specific +5.31% move**: found nothing dated closer than the
  month-old H1 earnings — no fresh news explains today's pop
  specifically. Reads as a technical bounce off the weekly MA200 test
  (see chart detail below), not a news-driven move — worth knowing
  since a technical-only bounce is less confirmed than, say, NIKL's
  fresh-earnings-driven dip-buy case.
- **ICT**: First PSE company past ₱2 trillion market cap. Mexico
  terminal expansion. 2025 revenue +18%, earnings +24.5%. "Strong Buy"
  from 13 analysts, target ₱1,099.
- **OGP**: Didipio mine life extended to 2037. $1.958B long-term
  investment plan confirmed. Solid 2026 production guidance. Real
  long-term visibility behind the clean uptrend.
- **Philweb (WEB)**: Q1 2026 return to profitability; Q2 swung from
  -₱0.013 EPS loss to +₱0.037, revenue +96%. **Two major capital
  injections**: ₱2.02B from Lance Gokongwei (major Philippine business
  figure) in June, and ₱4.226B on **Sep 9** (the day before this
  research) for a 30% stake in JKS Tech Solutions. Explains why it
  never offered a pullback — real, heavyweight news flow, not just
  technical momentum.
- **DMC** — the one softer read: Q1 2026 net income -2% YoY, FY2025
  net income -21% YoY, analyst fair value cut from ₱10.04→₱9.42. Still
  above current price, but tempers the "genuinely interesting
  long-term candidate" framing given to it earlier — worth weighing
  this against the technical bounce thesis, not just the chart.

## Current Holdings (already owned — not staged entries)

**Trigger: typing "positions"** means pull live current prices for
every symbol in this table (via filgit.com/MarketScreener/TradingView,
whichever's working that day) and report each against its cost basis,
unrealized %, and trailing-stop level on file — no need to ask what's
wanted, this is the standing request.

Positions the user is already holding, managed via the [Exit
methodology](#exit-methodology-partial-profit-take-then-trail-the-remainder)
above rather than the entry-side staging used for the watchlist proper.

| Symbol | Cost basis (real) | Current price | Unrealized | **Catalyst** | Partial take done? | Trailing stop (remainder) | Technical read |
|---|---|---|---|---|---|---|---|
| **LTG** | ₱11.333 (900 sh, real avg) | ₱15.16 (3:00 PM close, -0.26% today, range 15.10–15.18) | +33.78% | Q2 NI +24% YoY, rev +6.3%; dividend just paid (ex-date Sep 7), 8.2% yield | ✅ 30% sold at +20% | ₱14.29–14.52 (weekly ATR-based, 1–1.5x ATR14=0.46) — price still well above, stop not threatened | Genuine multi-year weekly uptrend (recovered from ~₱8-9 in 2022-23), now testing its own 2021 high — a confirmed weekly close above that old high would be a real breakout signal. Daily RSI neutral (50.3), weekly RSI neutral (52.2) — room to continue, not extended. |
| **SCC** | ₱37.7423 (800 sh remaining, real avg — was 1,600) | ₱17.50 (3:00 PM close, -1.80% today, range 17.38–17.96) | -53.63% | Coal-block auction risk dominates (contract expiry Jul 2027, DOE re-bid, terms being worsened) — see dedicated section. No 2026 dividend declared (expected ~May, skipped) | ✅ **50% trimmed 2026-09-11** — sold 800 sh @ ₱17.90, realized loss ≈ -₱15,873.84 gross (see Trade Journal) | Not set — no technical reversal signal to base one on | Long-term weekly downtrend, still unresolved: weekly MA200 (31.07) sits 75% above price, price down >50% from its 2022 peak (~₱38-40). Weekly RSI deeply oversold (28.00) — raises near-term bounce odds but is NOT a confirmed reversal. **The real driver, researched 2026-09-10: Semirara's core coal mining contract (COC No. 5, 10 blocks) expires July 2027, and the DOE has opened a competitive auction for those blocks — Semirara is NOT guaranteed to keep them.** New contract terms being drafted are worse for whoever wins (more mandatory domestic supply, larger government royalty). Auction repeatedly delayed (Feb→Aug→now Q4 2026). Semirara has already filed redundancy notices for 462 mine-site staff and cut 2026 production targets — the company's own actions signal real concern, not just market sentiment. **This undercuts the "cheap P/E, sound business" framing** — the low valuation (P/E 5.72, 7.01% yield) may be the market correctly pricing real contract-loss/worse-terms risk, not an overreaction. Full detail in the SCC section below. |
| **BLOOM** | ₱2.2567 (real fill, incl. fees — 1,000 sh, raw ₱2.24) | ₱2.23 (3:00 PM close, -0.45% today, range 2.20–2.30) | -1.18% | Q2 loss narrowed sharply (₱1.41B→₱345M YoY), EBITDA +35%, GGR +15% — genuinely supports the bottom-fish thesis | N/A — gave back today's earlier gain, now underwater again; partial-take rule doesn't apply until above cost | Not a trailing stop yet — **initial stop ₱2.05–2.10 active** (this is still the Starter tranche; see watchlist detail for the Confirmation-add trigger, still pending) | Early-stage/speculative bottom-fish, unconfirmed on both timeframes — see full [BLOOM entry](#bloomberry-resorts-corp-bloom) below for the setup. This is the Starter-only fill; sizing and risk still match that tranche, not a full position yet. |
| **BPI** | ₱103.6050 (real fill, incl. fees — 20 sh, 2 board lots) | ₱103.10 (3:00 PM close, -0.96% today, range 102.60–104.00) | -0.49% | Q1 miss vs forecast but +1.7% YoY NI; 2026 outlook targets high-single-digit growth | N/A — not yet in profit | Not a trailing stop yet — **initial stop ₱101.00–101.50 active** (Starter tranche; Confirmation-add still pending) — price is now within ~1.5% of the stop's top end, worth a closer watch | Trend pullback/continuation tier, testing daily MA50 (103.46) — see full [BPI entry](#bpi--bank-of-the-philippine-islands) below. Starter-only fill so far. |
| **NIKL** | ₱4.6738 (real fill, 1,000 sh, 2026-09-11) | ₱4.54 (3:00 PM close, -5.02% today, range 4.52–4.75) | -2.86% | H1 2026 NI +93% YoY to ₱4.06B, EBITDA +67%; tight nickel supply/demand tailwind | N/A — **T1-full-exit rule applies** (trader-not-investor, no partial take — see Exit methodology) | **Initial stop ₱3.90–3.95 active** (ATR-based, ~1.5x ATR14 below MA50) — still well clear, ~14-19% below current price | **Fresh chart confirms 2026-09-11**: a pullback off a local top (~4.9-5.0), not a trend break — still above MA20/50/200, RSI cooled from overbought (70.39→59.20), which is healthy, not alarming. See full [NIKL entry](#nickel-asia-corp-nikl) below. Still just the Starter — price hasn't reached the ₱4.25–4.45 confirmation-add zone yet. |

**Capital tracking (real, as of this fill):** BLOOM ₱2,256.70 + BPI
₱2,072.10 = **₱4,328.80 deployed**. User-reported cash on hand (before
the SCC trim): **₱4,353.23** — implies starting capital was ~₱8,682,
not exactly ₱8,000 as earlier estimated; using the user's real
reported numbers as authoritative going forward, not the earlier
planning estimate.

**Updated 2026-09-11 — SCC trim executed:** sold 800 sh @ ₱17.90,
gross proceeds ₱14,320.00. **Updated again same day — NIKL Starter
bought**: 1,000 sh @ ₱4.6738 = ₱4,673.80. **Real cash on hand,
user-reported after both: ₱13,942.** (Cross-check: ₱4,353.23 +
₱14,320.00 gross SCC proceeds − ₱4,673.80 NIKL cost = ₱13,999.43 —
the user's real ₱13,942 is ₱57.43 lower, consistent with real selling
fees on the SCC trim not being in the gross-proceeds estimate. Using
the user's real reported ₱13,942 as authoritative going forward, not
the derived estimate.)

**Portfolio concentration, recomputed with NIKL added:** total
portfolio value (positions + real cash) ≈ LTG ₱13,644 (900×15.16) +
SCC ₱14,320 (800×17.90) + BLOOM ₱2,280 (1,000×2.28) + BPI ₱2,068
(20×103.40) + NIKL ₱4,690 (1,000×4.69) + cash ₱13,942 ≈ **₱50,944**.
**Two names now sit inside the 25-30% flag band, not just one**:
**SCC ~28.1%** (down hard from 61.4% pre-trim, but still at the edge,
not comfortably clear) and **LTG ~26.8%** (hadn't been flagged before
— it's simply grown into this range as the stock has run, not from
any new buying). NIKL itself is a modest ~9.2% of portfolio, BPI
~4.1%, BLOOM ~4.5% — no sizing concern on either of those two.

**Redeployment plan, stated 2026-09-11**: the ₱13,942 cash on hand
(from the SCC trim) is earmarked for Confirmation-add tranches on
existing Starters, or new staged entries from the Summary table, once
their stated triggers actually fire — not sitting idle by default, but
also not deployed ahead of confirmation. As of the last price check,
**none of the pending triggers have fired yet**:
- BPI Confirmation-add: needs a close above EMA10 (104.63)/VWAP
  (104.33) or no-fresh-low candle — last close ₱103.10, below both.
- BLOOM Confirmation-add: needs a close above ₱2.34 (EMA10) or
  no-fresh-low candle — last close ₱2.23, below it.
- NIKL Confirmation-add: needs a pullback into ₱4.25–4.45 — last
  price ₱4.54, hasn't reached that zone.
- DMC: needs a weekly close back above ₱8.19 (MA20) — last price
  ₱8.14, just below, closest of the group to firing.
- CNPF Confirmation-add: needs a pullback into ₱32.37–32.48 — last
  price ₱33.70, today's own extended candle, hasn't pulled back.
- ICT/OGP/Philweb: none have pulled back into their stated entry
  zones yet either.

Re-check this list whenever "positions"/"summary" is run — flag
explicitly the moment any of these actually trigger, since that's the
point where this cash would actually move.

A/N: LTG and SCC cost basis updated 2026-09-10 to the user's real
average fill prices (900 sh @ ₱11.333, 1,600 sh @ ₱37.7423) — these
cross-check well against the earlier back-calculated estimates (+33.60%
vs. the originally-stated +33.59%; -52.73% vs. -52.87%, the small
remaining gap just normal price drift between when the % was first
reported and now), so the earlier estimates were reliable, but real
numbers are now on file and authoritative going forward.

**Position sizes, now known:** LTG 900 sh (~₱10,200 cost basis), SCC
**800 sh remaining post-trim** (~₱30,194 cost basis, was 1,600 sh/
~₱60,388 pre-trim) — both far larger than the ~₱8,682 trading budget
being used for BPI/BLOOM, confirming these are separate,
pre-existing holdings, not part of the same capital pool.

### Semirara Mining and Power Corp. (SCC) — full detail

**Portfolio context (superseded 2026-09-11 — trim executed):** this
originally read ~81% of invested capital (cost-basis measure) / 61.4%
of current portfolio value, down -52.73%, an unresolved
portfolio-construction issue. **Resolved in part**: the user sold 800
of 1,600 shares @ ₱17.90 on 2026-09-11, cutting SCC to ~28.1% of
portfolio value (see Capital tracking above and the Trade Journal log
entry). Still the largest single position and still carries no
technical stop — the trim addressed concentration, not the underlying
auction-risk thesis, which remains unresolved on the remaining 800
shares.

**The real catalyst/driver (researched 2026-09-10, prompted by user
tip "scc has bidding on going"):** Semirara's coal mining business
runs on a government-granted Coal Operating Contract (COC No. 5,
covering its core 10 coal blocks), which **expires July 2027**. The
Department of Energy has opened a **competitive auction** for those
same blocks — Semirara is not guaranteed to retain them; a competitor
could win instead.

- **Timeline, repeatedly delayed**: originally slated to launch ~Feb
  27, pushed to bid-submission around August, delayed again in
  mid-August to **Q4 2026** ("at least two more months" per Energy
  Secretary Sharon Garin). Given this pattern, further delay past Q4
  wouldn't be surprising — real uncertainty likely persists for months
  yet, not weeks.
- **New terms are being drafted worse for whoever wins**: DOE wants "a
  larger share of Semirara's output for local use" (domestic sales
  have historically realized lower prices than export) and a bigger
  government royalty share. Even a Semirara win under the new terms
  would likely be less profitable than the current arrangement.
- **Semirara's own actions signal real concern, not just market
  sentiment**: the company filed redundancy notices for 462 mine-site
  employees and cut 2026 production targets — this is the business
  itself hedging against the outcome, not just its stock price
  reacting to noise.
- **One mitigating data point**: Energy Secretary Garin called SMPC "a
  very qualified candidate" for the bidding round — not a guarantee,
  but not a dismissal either.
- **Separately**, industry estimates put remaining mine life at the
  existing blocks under 10 years regardless of the auction outcome —
  a longer-horizon consideration independent of the 2027 contract
  question.

**What this changes:** the "cheap P/E (5.72), 7.01% yield = real
counterweight to the bad chart" framing used earlier needs revision —
a low valuation on a company facing genuine risk of losing its core
operating asset, or winning it back on materially worse terms, may be
the market pricing the risk correctly rather than an overreaction
worth buying into. This doesn't resolve the hold/trim/exit decision on
its own, but it removes some of the "it's just oversold, fundamentals
are fine" comfort that decision was resting on.

**Still no technical stop or decision framework on file for this
position** — see the three options laid out in conversation 2026-09-10
(trim for portfolio-risk reasons independent of the chart, hold with a
defined stop such as a close below the 52-week low ₱15.90, or hold
deliberately as an income position with eyes open on the risk). Update
this section once the user decides.

**Dividend check (2026-09-10):** No dividend declared for 2026 at all.
Last paid ₱1.25/share, Nov 20, 2025. SCC has historically paid roughly
every 6 months, which would have implied one around May 2026 — it
didn't happen. Consistent with the cash-conservation signals already
found (cut 2026 production targets, 462 redundancy notices). **The
7.01% yield figure cited earlier is trailing, not a current guarantee**
— the income part of the "cheap valuation + solid yield" hold case is
weaker than the raw number implies, since this year's expected payment
hasn't shown up.

**Decision update — ✅ EXECUTED 2026-09-11.** Planned 2026-09-10 as a
50% trim (800 of 1,600 shares), confirmed filled the next day: 800 sh
@ ₱17.90 (vs. the ~₱17.84 planning estimate — essentially matched).
Gross proceeds ₱14,320.00, realized loss ≈ -₱15,873.84 gross (vs. the
~₱15,978 estimate — also close), fees not yet netted out. Post-trim
concentration: **~28.1% of portfolio value** (see Capital tracking
above), landing inside the earlier 31-44% estimated range's low end.
Logged in full in `TRADE_JOURNAL.md`. Still the largest single
position, still no technical stop on the remaining 800 shares — the
auction-risk thesis itself is unresolved and unaffected by this trim.

A running log of charts posted in conversation that were read as **nearing
a potential entry** — not a record of every chart reviewed. Names read as
already extended (chasing risk), directionless, or actively breaking down
are discussed in the conversation at the time but are NOT added here —
this file is a watchlist, not a chart-review archive.

Every entry below is a **discretionary technical read off a pasted
TradingView screenshot** — not backtested, not a systematic signal from
this project's tested engines (unlike `cryptobot/`'s strategies). Entry
price ranges are read off the chart's own moving averages/recent
levels, not derived from a validated system. Treat accordingly.

Each entry: the setup as read at the time, the entry range(s) that would
confirm it, and what invalidates it. When a name's status changes on a
later chart (confirms, fails, or gets extended), update its entry here
rather than duplicating a new one — keep one entry per symbol.

**Risk tier** (added once BLOOM's weekly context showed these aren't
all equivalent): every entry is tagged one of —
- **Trend pullback/continuation** — an established trend (weekly-
  confirmed) offering a pullback or breakout entry. The lower-risk
  category.
- **Early-stage / speculative bottom-fish** — a name recovering off a
  major decline, weekly chart still shows large overhead resistance,
  no fundamental context on why it fell. Same discretionary-entry
  logic, meaningfully higher risk — don't read as equivalent
  confidence to the pullback/continuation tier just because it's in
  the same file.

**Horizon** (added given the user's read that PSE is currently in a
bear market — not independently verified against the PSEi index
itself, only individual stock charts, so applied as a conservative
default rather than a confirmed premise): each entry also gets a
short-term vs. long-term call, based on two separate questions that
don't always agree —
1. Is the *technical setup* itself a defined, short-term trade, or an
   already-confirmed trend worth holding through?
2. Does the *company* even support a long-term hold — profitable with
   real earnings (a sane P/E) and a dividend, vs. speculative/
   unprofitable (negative P/E, no dividend)?

In a bear-market backdrop specifically: prefer short-term, defined-risk
trades over new long-term commitments generally, and be extra cautious
holding unprofitable/non-dividend names through a broader downturn
regardless of how good the chart looks.

---

## BPI — Bank of the Philippine Islands
- **Risk tier: Trend pullback/continuation** (weekly shows a real but
  modest overhang — MA200 ~10% above price, not the 80%+-decline kind)
- **Reviewed:** 2026-09-08, updated 2026-09-09 (daily+weekly, +VWAP/MACD/ATR) · **Price at review:** ₱103.90
- **Setup:** Rallying off a June low (~₱92) on the daily chart — but the
  weekly chart (added 09-09) shows this is a bounce inside a much bigger
  decline: BPI peaked ~₱148 in 2024 and fell to a 52w low of ₱87. Weekly
  MA50 (105.51) and MA200 (114.49) are both still above price — the
  daily "reversal" hasn't been confirmed on the higher timeframe yet.
  Today (09-09) pulled back right onto daily MA50 (103.46), the
  pullback entry zone, now live.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: on any touch/close within **₱102.50–104.00** (holding
    daily MA50, 103.46), stop active immediately at ₱101.00–101.50
    (ATR(14)=2.76, ~1x ATR below support).
  - **Confirmation add**: the first daily candle that doesn't make a
    fresh low vs. the prior day, or a close back above EMA10 (104.63)/
    VWAP (104.33) — add here even if price has moved off the starter
    fill.
  - Breakout entry: **₱108.50–110.00** on the daily chart — but treat
    as partial confirmation only. Full confirmation needs the WEEKLY
    chart to reclaim weekly MA50 (105.51) and hold, with weekly MA200
    (114.49) as the real longer-term hurdle above that.
- **Take-profit:** T1 **₱108–109** (prior local high, ~2.6:1 R:R from
  the pullback entry) · T2 (stretch, if trend continues) **₱114–115**
  (weekly MA200 confluence).
- **Invalidation:** a daily close below ~₱101 voids the pullback read;
  a rejection back below ~₱109 after a breakout attempt voids that read.
- **Horizon: Short-term (swing) preferred.** Blue-chip, profitable
  (P/E 8.25), dividend payer (4.68% yield) — a defensible long-term
  accumulation candidate on its own fundamentals, but the current setup
  is only a daily-level pullback with the weekly trend still
  unconfirmed (~10% below weekly MA200). Treat as a defined-risk trade
  first; only reconsider for a long-term add if the weekly chart
  actually reclaims MA50/MA200.

## Philweb Corp. (WEB)
- **Risk tier: Trend pullback/continuation** (weekly-confirmed —
  the cleanest of the three)
- **Reviewed:** 2026-09-08, updated 2026-09-09 (daily+weekly, +VWAP/MACD/ATR) · **Price at review:** ₱15.00
- **Setup:** Fresh breakout leg out of a multi-month base (Mar-Jul
  consolidation), full bullish MA stack, RSI 66.29 (not extreme).
  Today's candle itself is the extended one — closed at the day's high
  after a +4.17% move, no retest yet. **Weekly chart (09-09) confirms,
  doesn't just add caution** (unlike BPI): weekly RSI 67.25, MACD
  solidly positive on a sustained multi-quarter arc, price massively
  above weekly MA50 (9.94)/MA200 (4.04) — this is a real, weekly-level
  uptrend, not a daily-only illusion.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: already-live chase/starter (smaller size), current
    levels **₱14.70–15.20** — sized down since it's the unconfirmed
    breakout candle itself, OR on any touch into the pullback zone below.
  - **Confirmation add**: a hold in the **₱14.20–14.45** EMA10
    (14.42)/MA20 (14.26)/VWAP (14.90) zone, confirmed by the next
    candle not making a fresh low. ATR(14)=0.48 puts the stop at
    **~₱13.50–13.70** (~1.5x ATR below the zone, just under MA50) —
    active as soon as any tranche fills, not just on confirmation.
- **Take-profit:** **₱16.00–16.50** — no clear overhead resistance to
  target since price is making new highs, so this is an R-multiple-
  based target (~2.5:1 off the pullback entry/stop) rather than a
  structural level. Trail the stop up as it runs rather than treating
  this as a hard ceiling.
- **Invalidation:** a close below ~₱13.50 turns the pullback from
  "healthy retest" into "setup failing" — not a buy at that point.
- **Horizon: Short-term only.** Momentum/speculative profile — negative
  P/E (-198.62, currently unprofitable), no dividend. The move is real
  and weekly-confirmed, but with no earnings or income support
  underneath it, this is a trade to manage with a stop, not a name to
  hold through a broader market downturn. Take gains into strength;
  don't treat as a core long-term position regardless of how strong the
  chart looks.

## Bloomberry Resorts Corp. (BLOOM)
- **Risk tier: Early-stage / speculative bottom-fish** (down ~80% from
  2024 highs, weekly MA200 ~180% above price, no fundamental context on
  the decline — do not read as equivalent confidence to BPI/Philweb)
- **Reviewed:** 2026-09-09, corrected same day (daily+weekly, +VWAP/MACD/ATR) · **Price at review:** ₱2.34
- **Setup:** Daily chart shows a real MA-compression-then-reclaim (MA150
  2.17, MA50 2.17, MA200 2.30, MA20 2.32, EMA10 2.34 all converged at/
  below price) — but the **weekly chart corrects the read materially**:
  weekly MA200 = **6.59**, roughly 180% above current price. BLOOM fell
  from ~₱11-12 (2024) to a 52w low of ₱1.60 — an 80%+ decline — and
  today's bounce is early-stage relative to that, weekly RSI (53.29)/
  MACD (near zero) confirm just-stabilizing, not a confirmed weekly
  uptrend. Closer to BPI's "bounce inside a bigger decline" pattern than
  to Philweb's weekly-confirmed strength — and more extreme than BPI's
  version of that same gap.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: on any touch/close within **₱2.17–2.32** (the
    converged daily MA cluster), stop active immediately at
    **~₱2.05–2.10** (ATR(14)=0.13, ~1.5x ATR below, under MA50/MA150).
  - **Confirmation add**: the next candle not making a fresh low, or a
    close back above ₱2.34 (EMA10) — add here even at a slightly
    higher price than the starter.
  - Breakout entry, now two steps not one: first weekly MA50 (**~₱2.45**,
    only ~4.5% above current price — the nearer, more relevant hurdle),
    then confirmation through the **₱2.60** August high. Clearing 2.60
    without holding 2.45 first is a weaker signal than previously stated.
- **Take-profit:** T1 **₱2.45** (weekly MA50 — weak R:R alone, ~1.2:1,
  treat as a checkpoint not an exit) · T2 **₱2.60** (August high,
  ~2.1:1 R:R — the more meaningful target). Weekly MA200 (6.59) is far
  too distant to be a realistic near-term target.
- **Invalidation:** a close back below ₱2.05 undoes the pullback read.
  Weekly MA200 (6.59) is real overhead resistance but not a near-term
  factor — treat this as an early-stage speculative recovery, not a
  name that's proven itself the way Philweb has.
- **Horizon: Short-term only, smallest size.** Negative P/E (-5.35), no
  dividend, still ~80% below 2024 highs with a large unconfirmed weekly
  overhang. In a bear-market backdrop this is the last name on the list
  to hold with long-term conviction — treat any position as a defined-
  risk trade, exit per the plan, don't average down if it goes against
  you.

## DMCI Holdings, Inc. (DMC)
- **Risk tier: Early-stage / speculative bottom-fish** (same posture as
  BLOOM — unconfirmed on both timeframes — but a materially better
  fundamental profile: real earnings, real dividend, not unprofitable).
- **Reviewed:** 2026-09-10, ATR added same day · **Price at review:**
  ₱7.97 · **ATR(14): 0.20 daily / 0.45 weekly**
- **Note on sourcing accuracy — TWO corrections on this name, not one:**
  (1) the prior MA-only screen (MarketScreener) said DMC was "above
  MA50, RSI 54.86 neutral, turning up" — the first chart contradicted
  that (below every MA, RSI oversold at 32.18/40.30). (2) **That first
  chart itself was then found to be wrong on the daily timeframe** —
  this ATR re-paste shows daily MA20/EMA10 both at 7.87 and RSI 58.14,
  nothing like the original 9.44/9.26/32.18. Weekly RSI matched exactly
  both times (40.30), which is the tell: a 20-day average can't
  genuinely shift ~15% in one session, so the first chart's *daily*
  indicator panel was almost certainly caught by the same stale-cursor
  issue already flagged for its price readout at the time (it was
  sitting on a "29 May" hover position), not just the top price line.
  This fresh paste is the trustworthy one. **Lesson: a hover/crosshair
  artifact can silently corrupt the whole indicator panel, not just the
  headline price — worth a beat of skepticism whenever a chart's own
  numbers look internally inconsistent with the visual pattern.**
- **Setup:** A hard decline from ~₱10.30 (Mar 2026) to a 52-week low of
  ₱7.01, now attempting an early bounce. **Materially further along
  than previously stated**: daily price (7.97) is now above BOTH EMA10
  and MA20 (7.87 each), RSI a healthy 58.14 — not still oversold below
  every average. Weekly still testing MA20 (8.19) from just below,
  unconfirmed on that timeframe specifically. Real tailwinds
  distinguishing this from a pure speculative bottom-fish: **BPI
  Securities upgraded to Buy in August with an ₱11 target** (~38%
  above current price), and fundamentals are genuinely cheap — P/E
  6.22, dividend yield 9.59% (well-covered enough to be rated, not a
  yield-trap red flag on its face, though worth your own diligence on
  sustainability given the size of the payout).
- **Setup:** A hard decline from ~₱10.30 (Mar 2026) to a 52-week low of
  ₱7.01, now attempting an early bounce — currently testing weekly MA20
  (8.19) from just below, unconfirmed. Real tailwinds distinguishing
  this from a pure speculative bottom-fish: **BPI Securities upgraded
  to Buy in August with an ₱11 target** (~38% above current price), and
  fundamentals are genuinely cheap — P/E 6.22, dividend yield 9.59%
  (well-covered enough to be rated, not a yield-trap red flag on its
  face, though worth your own diligence on sustainability given the
  size of the payout).
- **Entry ranges (staged — see Entry methodology above, extra caution
  given the unconfirmed-reversal tier):**
  - **Starter (keep small)**: current levels/today's range **₱7.86–8.02**
    — this IS the live weekly-MA20 test, not a future zone to wait for.
  - **Confirmation add — corrected level, likely already satisfied
    today:** a weekly close back above 8.19 (MA20), OR a daily close
    back above the **real** EMA10 (7.87, not the erroneous 9.26 from
    the first chart) — today's close (7.97) already sits above both
    daily EMA10 and MA20. Worth treating the daily confirmation as
    effectively live now, not "~15-18% away" as previously stated.
  - **Stop, corrected with real ATR (2026-09-10):** ATR(14)=0.20 daily
    → 1–1.5x below the MA20/EMA10 cluster (7.87) = **~₱7.57–7.67**.
    Close to the original structural guess (₱7.50) — a modest
    tightening, not a big miss like ICT's.
- **Take-profit:** T1 **₱9.50–9.71** (weekly/daily MA50 confluence,
  ~3.5:1 R:R) · T2 (stretch) **₱10.65–11.00** (daily MA150/200
  confluence, roughly matching BPI Securities' ₱11 target, ~5.7:1 R:R).
- **Invalidation:** a close below ~₱7.57–7.67 undoes the bounce read; a
  close below the 52-week low (₱7.01) undoes the broader bottoming
  thesis.
- **Horizon: Short-term entry (defined-risk trade on an unconfirmed
  bounce), but a genuinely interesting long-term candidate on
  fundamentals** — real earnings, real dividend, analyst-backed upside
  case — IF the technical bottom actually holds. Unlike BLOOM, the
  long-term case here doesn't depend only on the chart resolving well;
  it's also supported independently by cheap valuation and income. Still
  size the trade for what the chart currently shows (unconfirmed), not
  for the fundamental story alone.

## Nickel Asia Corp. (NIKL)
- **Risk tier: Trend pullback/continuation** (cleanest of the three so
  far — no meaningful weekly overhang)
- **Reviewed:** 2026-09-09 (daily+weekly, full indicator set) · **Price at review:** ₱4.72
- **Setup:** Recovery leg since a June low, full bullish MA alignment on
  BOTH daily (price above MA200 4.40/EMA10 4.40/MA20 4.25/MA50 3.93) AND
  weekly (weekly MA200 = 4.35, already below price — no BPI/BLOOM-style
  overhang). Weekly RSI calm (58.31), MACD near-neutral. 52w range
  3.14-5.73 — well below its own 52w high, real room left. Daily
  RSI = 70.39, right at the overbought line after a strong +2.83% day —
  the one caution, matches Philweb's "hot candle, wait for the pullback"
  situation.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: on any touch within the shallow zone **₱4.60–4.70**
    (VWAP) or current levels **₱4.70–4.80**, smaller size given daily
    RSI was at 70 (overbought line) at last review.
  - **Confirmation add**: a hold in the deeper zone **₱4.25–4.45**
    (EMA10/MA20), confirmed by the next candle not making a fresh low.
    ATR(14)=0.19 puts the stop at **~₱3.90–3.95** (~1.5x ATR below,
    just under MA50) — active as soon as any tranche fills.
- **Take-profit: T1 ₱5.20–5.40 — under the current T1-full-exit rule
  (trader not investor, see Exit methodology), this is a full exit,
  not a partial take.** T2 (stretch) ₱5.65–5.73 (52-week high, ~3.2:1
  R:R) is now moot for this position specifically — kept for reference
  only in case the exit rule changes again, not the active plan.
- **Invalidation:** a close below ~₱3.90 undoes the pullback read.
- **Horizon: Short-term (T1 full-exit) — superseded 2026-09-11.**
  Originally tagged "Both," reflecting NIKL's genuinely strong
  long-term case (profitable, P/E 8.09, dividend payer 4.39% yield,
  cleanest technical structure of the four reviewed). That fundamental
  quality is still real and still the reason this ranked #1-3 on
  conviction — but per the unified trader-not-investor exit rule now
  active for both projects, this position is managed as a short-term
  trade to a full exit at T1, not a long-term hold, regardless of how
  good the underlying business is. Long-term quality stays useful
  context, not the operative plan.
- **✅ FILLED 2026-09-11 — Starter, 1,000 sh @ ₱4.6738 avg.** Landed in
  the shallow starter zone (₱4.60–4.70) exactly as planned, on the
  first real pullback since this name was added. Stop ₱3.90–3.95
  active immediately per the Entry methodology. Logged in
  `TRADE_JOURNAL.md`.
- **Catalyst refresh, 2026-09-11** (today's -1.88% pullback put price
  right into the shallow starter zone — see summary table): H1 2026
  net income +93% YoY to ₱4.06B, EBITDA +67% YoY to ₱8.68B (published
  Aug 7, 2026) — genuinely fresh and strong, though Q1 2026 standalone
  was weak (-26% YoY), so Q2 alone carried H1's strength. Full detail
  and sourcing in the Fundamental Catalysts section above. Nothing
  found that explains today's specific dip as company-driven — reads
  as a normal pullback into the stated zone, not a reaction to bad
  news.
- **Fresh daily chart, 2026-09-11 close** (real numbers, not the
  provisional filgit price-only read): O 4.75, H 4.75, L 4.52, **C
  4.54 (-5.02%)** — a sharp single-day drop off what the chart shows
  was a run toward ~4.9-5.0 over the prior sessions. **Reads as a
  pullback off a local top, not a trend break**: price still above MA20
  (4.31), MA50 (4.00), and MA200 (4.41) — the full bullish MA stack
  from the original review is intact. **RSI14 = 59.20**, down from the
  70.39 flagged as overbought at the original review — this is the
  overbought condition resolving via a healthy pullback, not a
  breakdown signal. One short-term caution: today's close sits just
  below both EMA10 (4.53, essentially a tie) and session VWAP (4.60) —
  worth watching whether the next session makes a fresh low below
  today's 4.52 or holds. NFB/s -684.92K (net foreign selling today),
  a real data point, not independently alarming. **Position status**:
  still just the Starter — price hasn't reached the ₱4.25–4.45
  Confirmation-add zone yet; if it gets there, that's the pre-planned
  second tranche, not a stop concern. Stop (~₱3.90–3.95, just under
  MA50) unchanged and still ~14-19% below current price.

## International Container Terminal Services, Inc. (ICT)
- **Risk tier: Trend pullback/continuation — cleanest weekly structure
  of anything on this list.** No overhang at all: weekly MA50 (730.53)
  and MA200 (414.59) both sit far below current price, unlike BPI/
  BLOOM's still-unresolved weekly gaps.
- **Reviewed:** 2026-09-10, ATR/MACD added same day (daily+weekly, full
  indicator set) · **Price at review:** ₱975.00 · **ATR(14): 30.15
  daily / 65.65 weekly**
- **Setup:** A long, sustained rally off a ~₱700 base (Mar 2026) to
  ₱975 now — daily MAs fully stacked bullish (MA20 947.88 < MA50 961.55
  < price, MA150 820.09 and MA200 760.80 far below). RSI14 55.74 daily /
  63.68 weekly — healthy, nowhere near overbought despite the size of
  the move. Chart shows a real Aug consolidation/pullback (price dipped
  toward ~₱900-920) before today's strong reclaim: opened 958, ranged
  956-984, closed 975 (+1.88%), right at session VWAP (971.67). Weekly
  candle this week is also a strong +4.33% (943.50→975) bar. 52w range
  471.20-1,049.00 — price at ~93% of the way to the 52w high but not
  there yet, ~7% of room left. P/E 28.33 (real earnings, but a notably
  higher multiple than anything else on this list — a quality/growth
  premium, not a value entry), div yield 1.81%.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: on any touch/close within **₱947–962** (the daily
    MA20/MA50 cluster) — not live today, since today's candle ran away
    from that zone rather than testing it.
  - **Confirmation add**: the next daily candle not making a fresh low
    vs. the prior one, or a close back above EMA10 (944.94) — add here
    even at a slightly higher price.
  - **Stop, corrected with real ATR (2026-09-10):** ATR(14)=30.15 →
    1–1.5x ATR below EMA10 (944.94) = **~₱900–915**. This is
    meaningfully looser than the original structural estimate
    (₱938–942) — that guess was too tight relative to ICT's actual
    daily volatility (ATR ≈3.1% of price). Genuinely good confluence
    though: the ATR-derived level lands almost exactly on the Aug swing
    low (~₱900-920) already flagged qualitatively, confirming that zone
    is the real support, not just a round-number guess.
  - Chase/continuation entry: current levels **₱975–984** (today's
    range) — treat as sized-down, same caution as Philweb/NIKL's "hot
    candle" situations; today's candle itself is the extended one.
- **Take-profit:** T1 **₱1,000** (round-number/psychological level, no
  precise prior structure between here and the 52w high — ~3:1 R:R off
  the pullback entry) · T2 (stretch) **₱1,049** (52-week high, ~6.3:1
  R:R).
- **Invalidation:** a close back below ~₱900–915 (the ATR-confirmed
  stop) undoes both the pullback entry and the broader uptrend thesis —
  these two levels have converged now that the stop is properly sized,
  unlike the original structural guess which treated them as separate.
- **Horizon: Both — short-term entry on the pullback, reasonable
  long-term candidate.** Profitable, dividend payer, by far the
  cleanest weekly trend structure reviewed so far — but the P/E (28.33)
  is meaningfully richer than BPI/NIKL/APX's single-digit-to-low-teens
  multiples, so this is a "pay up for quality/momentum" hold, not a
  cheap long-term accumulation the way NIKL is.

## OceanaGold (Philippines), Inc. (OGP)
- **Risk tier: Trend pullback/continuation** — clean, no overhang.
- **Reviewed:** 2026-09-10 (daily+weekly, MA20/50/150/200+EMA10+VWAP+RSI,
  no ATR shown) · **Price at review:** ₱38.00
- **Note on sourcing accuracy:** unlike DMC, the prior MA-only screen
  for OGP checked out — RSI14 (64.58) and MA50 (34.23) both matched the
  real chart exactly. Confirms the correction discipline works both
  ways: don't blanket-distrust a computed screen either, just verify
  before acting on it.
- **Setup:** A genuine, gradual multi-quarter climb from ~₱12-14 (mid-
  2025) to ~₱38-40 now — not parabolic like FGEN, real pullbacks along
  the way (a real dip toward ~₱32-34 in late Aug/early Sep already
  happened and has been reclaimed, visible on both timeframes). Daily
  MAs fully stacked bullish (MA20 36.65 < price, MA50 34.23, MA200
  34.22 — all below price). Weekly RSI 61.44 / daily RSI 64.58 — both
  healthy, not overbought. Weekly MA150/200 were hidden/not legible on
  this chart, so the long-term weekly overhang picture is incomplete —
  worth re-checking on a future chart if those become visible. 52w
  range 21.20-40.50 — price at ~94% of the way to the 52w high. P/E
  12.15, dividend yield 8.74% — genuinely attractive on both valuation
  and income, better than most names on this list.
- **Entry ranges (staged — see Entry methodology above):**
  - **Starter**: on any touch/close within **₱34.20–36.65** (the
    MA20/MA50/MA200 cluster) — not live today; price already reclaimed
    this zone and is running near the highs.
  - **Confirmation add**: the next daily candle not making a fresh low,
    or a close back above EMA10 (36.90) — likely already satisfied if
    price dips back into the zone and recovers same-day.
  - Chase/continuation entry: current levels **₱37.60–38.00** (VWAP/
    today's range) — sized down, same "hot candle" caution as
    Philweb/NIKL/ICT; today is a strong +2.4-2.7% day on both
    timeframes. R:R from here is meaningfully worse than from the
    pullback zone (see below) — the pullback entry is clearly preferred
    if it comes.
  - **Stop, corrected with real ATR (2026-09-10):** ATR(14)=1.09 daily
    / 2.59 weekly → 1–1.5x daily ATR below MA50/MA200 (34.23/34.22) =
    **~₱32.60–33.15**. Only a modest loosening from the original
    structural guess (₱33.50) — unlike ICT, that estimate was already
    reasonably close to the real ATR-based level. Weekly ATR
    independently confirms the broader ₱34-35 area (near weekly MA20,
    34.49) as real support too, cross-timeframe confluence.
- **Take-profit:** T1 **₱40.00** (round number/near 52w high, ~2.4:1
  R:R from the pullback entry) · T2 **₱40.50** (52-week high, ~2.7:1
  R:R). A clean break above 40.50 opens new territory with no prior
  structure — trail the stop rather than treating 40.50 as a hard cap.
- **Invalidation:** a close below ~₱32.60–33.15 undoes the pullback read.
- **Horizon: Both — short-term entry on the pullback, solid long-term
  candidate.** Profitable, meaningfully cheaper than ICT (P/E 12.15 vs
  28.33) with a much larger dividend (8.74% vs 1.81%) — a better
  value/income combination than ICT, though as a gold miner it carries
  the same commodity-price cyclicality caveat as NIKL/APX.

## Century Pacific Food, Inc. (CNPF)
- **Risk tier: Trend pullback/continuation, weekly still unconfirmed**
  — closer to BPI's "bounce inside a bigger decline" pattern than to
  ICT/OGP/NIKL's clean weekly-confirmed trends.
- **Reviewed:** 2026-09-11 (daily+weekly, MA200/MA20/MA50/EMA10/VWAP/
  RSI14/MACD/ATR14) · **Price at review:** ₱33.70 (+5.31% today, closed
  at the day's high)
- **Note on sourcing accuracy:** the initial MarketScreener MA/RSI
  screen (used to flag this name "worth a closer look") gave RSI14 =
  48.95 — the real chart shows **63.19**, a meaningful miss (though it
  didn't change the screening verdict here, since both readings are
  non-overbought). Also: the "day range" MarketScreener returned
  (₱31.70–32.35) didn't bracket even MarketScreener's own quoted price
  (₱33.70) — a stale-range artifact matching the pattern already seen
  on DMC. Worth the reminder: trust the real chart over the computed
  screen whenever they disagree, which is exactly why step 2's screen
  is provisional and step 4/5's chart is what actually decides.
- **Setup:** A hard decline from the 52w high (₱41.30) down toward the
  ₱28 area (Aug 2026, visible on the daily chart) has been reversing
  sharply the last several sessions, culminating in today's +5.31% bar.
  Daily: price (33.70) now above MA20 (32.48), MA50 (31.90), EMA10
  (32.37), and VWAP (33.05) — but still *below* daily MA200 (34.19),
  which is itself declining (a real overhang, not yet reclaimed).
  Weekly: price is landing almost exactly **on weekly MA200 (33.62)** —
  a genuine live inflection test — while weekly MA50 (34.64) sits just
  ~2.8% above as the next real hurdle. Weekly RSI 55.06 (neutral, room
  to run), weekly MACD histogram still negative (-0.93) but the MACD
  line (0.61) is above its signal (-0.32) — an early bullish
  crossover, not yet a confirmed weekly uptrend the way ICT/OGP/NIKL
  have. Today's own candle is the extended one — closed at the day's
  high after a +5.31% move, no retest yet, same "hot candle" caution as
  Philweb/NIKL/ICT's chase-day setups.
- **Entry ranges (staged — see Entry methodology above, extra caution
  given the unconfirmed-weekly tier and today's hot candle):**
  - **Starter (keep small, chase caution)**: current levels
    **₱33.50–33.70** if adding right away — sized down since this is
    the unconfirmed breakout candle itself, same treatment Philweb got.
  - **Confirmation add (preferred entry)**: a pullback into
    **₱32.37–32.48** (EMA10/MA20 daily cluster), confirmed by the next
    candle not making a fresh low. ATR(14)=0.86 puts the stop at
    **~₱31.00–31.20** (~1.5x ATR below the cluster, also just under
    daily MA50 at 31.90 — good confluence).
- **Take-profit: T1 ₱34.60–34.70** — real structural confluence
  (weekly MA50 at 34.64 and daily MA200 at 34.19 cluster together here,
  not an invented R-multiple level). **Full exit at T1 under the
  current T1-full-exit rule** — no partial take, no T2 beyond this;
  the 52-week high (₱41.30) is too far above to be a realistic T1-style
  target and isn't the plan here.
- **Invalidation:** a daily close below ~₱31.00–31.20 undoes the
  pullback read. **More decision-relevant than the stop itself**: a
  **weekly close back below weekly MA200 (33.62)** would undo the
  reversal thesis even before the daily stop is threatened — worth
  watching that level specifically, not just the stop price.
- **Horizon: Short-term (T1 full-exit rule).** Fundamentals are
  genuinely strong — real H1 2026 earnings growth, "Strong Buy"
  analyst consensus, a defensible staples business — but per the
  account's current trader-not-investor approach, this is managed as a
  short-term trade to a full exit at T1, not a long-term hold, same as
  every other position on this list now. See the Fundamental Catalysts
  section above for the full earnings detail and the honest note that
  nothing fresh explains today's specific move.

## Apex Mining Company, Inc. (APX)
- **Risk tier: Trend pullback/continuation**
- **Reviewed:** 2026-09-09 (daily+weekly, full indicator set) · **Price at review:** ₱16.80
- **Setup:** Genuine, moderate uptrend since a June low (~₱10.50) — not
  a parabolic spike like Atlas (AT) or IMI. RSI 61.64 daily / 58.89
  weekly, well off overbought. **Caution: today's candle is a real
  warning sign** — opened 17.50, made a marginal new high (17.66), then
  sold off hard to close at the day's low (16.80, -2.78%) on BOTH the
  daily and weekly chart (same candle) — a distribution/rejection
  pattern. Weekly MACD histogram visibly rolling from green to red in
  the last several bars. Not yet a confirmed reversal, but not
  something to treat as "just noise" either — wait for the next 1-2
  sessions to see where it actually stabilizes before trusting a
  support level. 52w range 8.05-18.46 — high in range (~83%) but not
  pinned at the top like AT was.
- **Entry ranges (staged — see Entry methodology above, extra caution
  here given the fresh distribution candle):**
  - **Starter (keep extra small)**: on touch into either **₱16.30–16.50**
    (EMA10, shallow) or **₱15.50–15.80** (MA20, deeper, preferred) — but
    since today's candle was an active rejection, not just a routine
    pullback, size this piece smaller than the other names' starters.
  - **Confirmation add (carries more weight than usual)**: the next
    candle not making a fresh low vs. today's 16.80 close. ATR(14)=0.75
    → stop **~₱14.20–14.40** (~1.5x ATR below MA20, just above MA50 at
    14.25), active as soon as the starter fills.
- **Take-profit:** T1 **₱17.50–17.66** (retest of today's high) — ✅
  **achieved 2026-09-10.** T2 (stretch) **₱18.46** (old 52-week high) —
  ✅ **also achieved/surpassed intraday 2026-09-10**, when price hit a
  new 52w high of ₱19.18 — the original 52w-high target is now stale.
  **Updated T3 (new stretch, 2026-09-10):** ₱19.70–20.00, R-multiple
  based (~3:1 off the original deep-entry/stop pair: entry ~15.65, stop
  ~14.30, risk ~1.35/share) since there's no prior structural resistance
  above the old 52w high to target instead — same reasoning as
  Philweb's stretch target. **Treat as a trailing reference, not a hard
  ceiling** — trail the stop up as the position runs rather than
  planning to exit fully exactly there.
  - **Trailing stop, now that the position is well past both original
    targets:** the original fixed stop (₱14.20–14.40) is now 20%+ below
    price and no longer protects much of the move. Trail instead —
    ATR(14) was 0.75 at original review (2026-09-09, likely stale by
    now); until a fresh ATR reading is pasted, use ~1.5x that (≈₱1.13)
    below the most recent swing low as a rough trailing reference, and
    tighten once a fresh chart with current ATR is available.
- **Invalidation:** a close back below ~₱14.20 undoes the *original*
  pullback thesis — but given the position has run well past that
  level, the trailing stop above is now the operative exit, not this
  original invalidation level.
- **Horizon: Short-term entry, reasonable long-term candidate.**
  Profitable (P/E 11.00), dividend payer (3.52% yield) — similar
  profile to NIKL. Same mining-sector cyclicality caveat as NIKL/AT
  apply to "long-term" here. **Play type updated to Quick** (see summary
  table) — the clean pullback character is gone now that it's broken to
  new highs; manage with tighter, faster risk discipline than the
  original swing-pullback framing assumed.

---

## Reviewed but NOT added (for reference — not maintained further)

- **IMI** (2026-09-08, ₱8.40) — already extended (+140% in <3 months,
  90%+ above 200MA, RSI 73.97) — chase risk, no near-entry level.
- **MBT** (2026-09-08, ₱65.90) — directionless range, below every MA,
  no clear setup either direction.
- **RCR** (2026-09-08, ₱6.75) — active breakdown, rejected off a
  resistance test, below every MA, fresh bearish momentum.
- **AT (Atlas Consolidated Mining)** (2026-09-09, ₱23.05) — the most
  extreme chase-risk chart reviewed so far, worse than IMI: RSI 82.30
  daily / 84.84 weekly (both deeply overbought simultaneously), price
  ~154% above daily MA200 and ~340% above weekly MA200, +10.82% today
  alone closing at the day's high, just ₱0.95 below its 52w high
  (24.00). Possible mining-sector-wide move (Philex/Apex/Atlas all
  showing up in most-active lists this week) — not confirmed, a
  hypothesis only.
- **PGOLD (Puregold Price Club)** (2026-09-09, ₱40.75) — different from
  the others above: not extended, not actively breaking down, but
  genuinely directionless — a real coiling/consolidation, not a clean
  rejection. All daily MAs (MA200 40.88, MA20 40.50, EMA10 40.41, VWAP
  40.58, MA50 40.33) clustered within ~₱0.50 of price with no clear
  stack order; weekly RSI 48.45, neutral. Been chopping in a ~38-42
  range for many months after a 2025 decline. **Worth watching for a
  resolution, not a clean pass**: a break above weekly MA20 (~42.31)
  with volume, or a breakdown below ~38, would turn this into a real
  setup either direction. Fundamentals solid if it resolves up (P/E
  9.78, div yield 4.87%).
- **FGEN (First Gen Corporation)** (2026-09-10, ₱26.00) — **reverses my
  own earlier MA-only screen**, which flagged FGEN as "worth a closer
  look" based on price above every MA with RSI not yet overbought. The
  actual chart shows why that screen was too coarse: this isn't a
  gradual uptrend like ICT's — weekly chart shows years of flat chop
  (~₱17-20) followed by a single violent vertical spike straight to
  ~₱30 within roughly a week, now consolidating at 26.00, still ~40%
  above weekly MA20 (19.58) and ~340% above weekly MA150/200 (~17.8).
  Daily RSI has already rolled over from a recent spike (chart shows it
  near ~78 days ago) down to a neutral 55.21 — momentum cooling, not
  building. This is the same underlying pattern as **AT (Atlas)**'s
  rejection above: a parabolic gap with no time spent building the
  move, meaning any "support" here is unproven, not weekly-confirmed.
  Real earnings and a fair valuation (P/E 8.80, div yield 2.96%) don't
  offset the chart risk — a name can be fundamentally fine and still be
  a bad entry if the technical structure is a fresh, untested spike.
  **Lesson for future computed-only screens**: MA/RSI numbers alone
  can't distinguish a healthy sustained uptrend (ICT) from a parabolic
  gap that happens to sit above its MAs (FGEN) — that distinction only
  shows up on the actual chart shape, so a computed screen's "worth a
  closer look" verdict should be treated as provisional until the chart
  confirms it, not acted on directly.
- **SGP (Synergy Grid & Development Phils.)** (2026-09-10, ₱24.70) —
  also reverses the earlier MA screen, but for a different, more mundane
  reason than FGEN/DMC: not a data error or a chart-shape mismatch, the
  setup simply deteriorated in the days since that screen. Price has
  broken **below both MA20 (27.30) and MA50 (27.38) on the daily chart**
  and below weekly MA20 (27.79)/EMA10 (26.90) too — closing near the
  session low on a sharp -3.33% day (-4.26% for the week), a real ~25-28%
  retracement off the ~₱32-34 July peak. This is a clean break through
  the short/medium MAs, not a test-and-hold — meaningfully worse than
  NIKL/ICT/OGP's pullback structure. **Data-quality note**: the weekly
  chart's MA200 line shows an extreme near-vertical drop from ~100+ to
  ~20 across 2024-2025 — almost certainly a listing/restructuring
  artifact in the historical data, not real price action, so weekly
  MA200 (12.94) isn't being treated as a meaningful level here.
  Fundamentals are genuinely attractive (P/E 3.83, div yield 5.59%,
  strong 1-year uptrend before this correction) — worth revisiting if
  price stabilizes and reclaims MA20/MA50, but not a pass right now.
- **V (Vantage Equities)** (2026-09-10, ₱1.21) — extreme chase risk,
  flagged from numbers alone without a chart: RSI14 67.75, but the real
  warning is the recent move itself — **+58.5% in one week, +62.5% in
  one month**, near the top of its 52w range (0.81-1.45). Same
  parabolic-spike signature as AT/FGEN.
- **ABG (Asiabest Group International)** (2026-09-10, ₱62.75) — extreme
  chase risk. RSI14 74.99 (confirmed overbought), +234% YTD, +1,993%
  over 3 years, sitting at 98.6% of its 52-week range (14-63.50). The
  most extended name reviewed by the numbers alone — worse than AT's
  RSI at screening time, on a much longer runway of gains.
