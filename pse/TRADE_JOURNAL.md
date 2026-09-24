# PSE Trade Journal — Wins, Losses, and What They Taught

A record of what actually happened after each trade action (entry,
partial take, stop-out, target hit, exit) — not just the plan, but the
outcome and the lesson. Companion to `WATCHLIST.md` (which is
forward-looking: setups, entries, targets) and `WATCHLIST.md`'s
"Working relationship" section (the standing analysis discipline this
journal exists to sharpen over time).

## How to log an entry

Add a new entry under "Log" below whenever a trade action resolves —
an entry fills, a stop gets hit, a target gets hit, a partial take
happens, or a position gets closed entirely. Use this template:

```
### YYYY-MM-DD — SYMBOL — ACTION (Entry / Partial take / Stop-out / Target hit / Exit)
- **Price:** ₱X.XX
- **Setup at the time:** (tier, play type, what the read was)
- **What actually happened:** (did the thesis play out as expected? did
  it stop out on noise or a real break? did it run past target?)
- **Plan adherence:** Yes / No — did the exit actually execute at the
  pre-committed level? If No, what happened in the moment (the real
  thought, not a retroactively tidied-up version) and how long the gap
  was between "price hit the level" and "order actually placed" (or
  "never placed"). This is a separate score from win/loss — a trade
  can be a win with No adherence (got lucky waiting) or a loss with
  Yes adherence (the plan was followed and still lost, which is a
  healthy, expected outcome of a probabilistic system, not a failure).
- **Lesson:** (what to repeat, what to adjust, what this confirms or
  contradicts about the methodology)
```

**Added 2026-09-15, mirrored from `us-stocks/TRADE_JOURNAL.md`** after
a real discipline gap surfaced there (a stated stop-check plan on NVDA
wasn't executed, in both directions per the user's own admission —
also happens when letting winners run past target, not just holding
losers past stop). Win/loss tracks whether the *market* cooperated.
Plan-adherence tracks whether *you* did. Same discipline now applies
here — BPI's recent close calls with its stop (two sessions within
~0.6-0.8% of breach, never actually triggered) are the first live test
this project will have of PSE-side adherence if it happens.

Keep entries honest — a lesson from a loss is as valuable as one from
a win, and a win for the wrong reason (right result, flawed process)
is worth flagging too, not just wins/losses at face value.

## Performance Summary (rolled up from the Log, refresh periodically)

Turns individual Log entries into aggregate numbers — win rate, average
R-multiple, total realized P&L — so the lessons compound instead of
just accumulating as isolated notes. Added 2026-09-10 per the user's
own framing of this journal as "a learning process," which needs
numbers, not just narrative, to actually measure.

**Current tally (2026-09-24) — honest about what's known vs. estimated:**

| Metric | Value | Note |
|---|---|---|
| Real closed-position events | 8 (LTG partial take, **SCC fully closed — 3 tranches**, BPI stop-out, BLOOM stop-out, **ICT stop-out**, **DMC stop-out**) | SCC fully closed across 3 sales; ICT closed 2026-09-21, DMC closed 2026-09-24, both after a deliberately-set stop plan triggered |
| Setup-accuracy events (not real money) | 1 (APX target hit) | Tracked separately — confirms/disconfirms the *analysis*, not a real trade outcome |
| Process-correction events | 1 (DMC data-quality) | Not a P&L event at all — a methodology lesson, separate from DMC's later stop-out |
| Realized P&L (real capital) | **~₱612 est. (LTG) + -₱15,873.84 (SCC #1) + -₱6,996.92 (SCC #2) + -₱7,076.92 (SCC #3) + -₱54.10 (BPI) + -₱176.70 (BLOOM) + -₱150 (ICT) + -₱198.03 (DMC) ≈ -₱29,914 net** | **All estimated/gross, not exact net** — LTG's execution price/date wasn't recorded at the time; the rest are gross, before selling fees. Ask the user for exact net fills if precision matters here. |
| Win rate, R-multiple average | Not yet meaningful | Sample size (8 real closed events, 1 win/7 losses) still small |
| **Plan adherence rate** | **2/2 real-time BPI/BLOOM tests still stand. SCC graded across 3 events: Yes, PARTIAL, NO. ICT graded ✅ YES — the stop was set, explicitly revisited and reaffirmed hours before it triggered, then honored exactly when price hit it. DMC graded ✅ YES — the zone was tested twice and held before finally triggering, and the stop was honored at the defined level once it broke, not reacted to early.** | Tracks whether pre-committed exit levels actually get executed, separate from whether the trade wins or loses — see "How to log an entry" above. |

**This section is only as good as the Log below it** — update this
table whenever a new entry is added there, not just when asked. Once
there are 5+ real closed-position events, start tracking win rate (%
of closed trades with positive realized P&L) and average R-multiple
(realized gain or loss ÷ the original risk-per-share defined at entry)
properly — not worth computing on this small a sample yet.

---

## Log

### 2026-09-24 — DMC — Stop-out (RESOLVED)
- **Price:** Sold 700 sh @ ₱7.65 (real fill), inside the ₱7.57-7.67
  stop zone set at entry. Cost basis was ₱7.9329/sh weighted avg (700
  sh, ₱5,553.03 total, filled 2026-09-18: 100 sh @ ₱7.95 + 600 sh @
  ₱7.93). Realized loss ≈ -₱198.03 gross (-3.57%).
- **Setup at the time:** The weakest fundamental story of the three
  names bought 2026-09-18 (Q1 NI -2% YoY, FY25 NI -21%, fair value cut
  ₱10.04→9.42) — flagged as such at entry, not a story that developed
  after the fact.
- **What actually happened:** The stop zone was tested intraday on
  2026-09-22 (low ₱7.63, inside the zone) but held — price recovered
  to ₱7.75 that session and ₱7.69 the next (2026-09-23) without
  breaking down further. Flagged across three consecutive refresh
  cycles (🔴 on 2026-09-22, downgraded to 🟡 on 2026-09-23) as an
  open, unresolved decision point. The stop finally triggered
  2026-09-24, with the sale executed inside the zone at ₱7.65.
- **Plan adherence: ✅ YES** — the stop was honored at the level it
  was set at, the same pattern as ICT's 2026-09-21 exit: a loss, but
  the process worked as designed. No holding past the zone hoping for
  a further bounce after two sessions of the zone being tested but not
  broken.
- **Lesson:** this is the second of the three 2026-09-18 fills (ICT
  being the first) to end in a stop-out, and DMC was flagged as the
  weakest fundamental story of the three at the time of entry — the
  price action ultimately confirmed that read. The zone held through
  two tests before finally breaking, which is a reminder that a
  flagged stop-zone test isn't automatically a signal to pre-emptively
  exit — the plan was to let the defined level trigger the decision,
  not to react to every approach toward it, and that discipline held
  here even though it took multiple sessions to resolve.

### 2026-09-21 — ICT — Stop-out (RESOLVED — the stop plan kept from Monday's review was honored)
- **Price:** Sold 10 sh @ ₱900 (real fill), the bottom of the
  ₱900-915 stop zone that was deliberately kept as-is during the
  2026-09-21 morning review (two data-grounded alternatives — a
  tighter ~₱895-900 stop or a structural ~₱870-875 stop — were
  presented and declined in favor of the original plan). Realized
  loss ≈ -₱150 gross (-1.64%) on the 10 sh position.
- **Setup at the time:** This was the position flagged at entry
  (2026-09-18) as having a near-zero stop cushion — bought at ₱915,
  right at what this account's own prior analysis called the stop
  level rather than the ₱947-962 pullback zone. Recovered briefly
  Monday morning (₱919, +0.44% unrealized) before fading back down
  and triggering the stop later the same session.
- **What actually happened:** The stop plan set on 2026-09-18, kept
  deliberately unchanged after a real re-examination on 2026-09-21,
  executed as designed when price came back down to it. This is a
  clean, same-day execution — no hesitation, no deviation.
- **Plan adherence: ✅ YES** — the stop was honored at the level it
  was set at, including after being explicitly revisited and
  reaffirmed just hours earlier. A genuinely good example: the
  position lost money, but the process worked exactly as intended.
- **Lesson:** The near-zero-cushion entry flagged on day one did
  eventually cost a stop-out, as the thin-margin risk always implied
  it might. But the discipline around it — flag the risk clearly at
  entry, revisit it explicitly when the risk materialized, and honor
  the plan once made — all held. A loss with clean process is a very
  different outcome than a loss from a broken one.

### 2026-09-21 — OGP — Add, 100 sh @ ₱36.40 (within the original entry zone)
- **Price:** Added 100 sh @ ₱36.40 to the existing 100 sh @ ₱36.65
  (2026-09-18 fill). New weighted avg cost ₱36.525/sh, 200 sh total,
  ₱7,305 total cost.
- **Setup at the time:** ₱36.40 is still within the originally
  stated ₱34.20-36.65 entry zone — this is a straightforward
  average-down within the same zone, not a new technical signal or a
  confirmation-add trigger firing. Stop remains ₱32.60-33.15,
  ~9.0-10.5% cushion from the new average cost.
- **What actually happened:** A same-session add, not yet resolved.
- **Plan adherence: N/A** — this wasn't executing a pre-committed
  staged-entry plan (the confirmation-add trigger for OGP was never
  defined as a specific price), just a discretionary add within the
  zone.
- **Lesson: N/A yet.**

### 2026-09-21 — WEB — Entry filled, clean zone fill, exactly as planned
- **Price:** Bought 400 sh @ ₱14.22 (real fill). Cost basis ₱5,688
  total. Filled near the lower part of the stated ₱14.20–14.45 entry
  zone — the user explicitly stated the plan ("ill enter web today
  when its near the lower range") and then executed it almost
  exactly, a clean example of plan-then-execute working as intended.
- **Setup at the time:** Real catalyst on file: Q2 swung to profit,
  revenue +96%, ₱2.02B + ₱4.23B capital injections (Gokongwei, JKS
  stake). Stop ₱13.50–13.70, ~3.9-5.3% cushion — a real, workable
  buffer, same category as OGP/DMC's clean fills, not ICT's
  near-zero-cushion situation.
- **What actually happened:** Filled as WEB tested its zone for the
  first time this cycle (it had approached but not entered the zone
  on several earlier checks). Not yet resolved.
- **Plan adherence: ✅ YES** — stated the plan, then executed it at
  essentially the exact level described, same session.
- **Lesson: N/A yet — but worth noting as a positive precedent**,
  the same way the 2026-09-10 LTG 30%-at-+20% take was flagged as
  real, working discipline independent of prompting.

### 2026-09-18 — DMC — Entry filled, two tranches, clean zone fill
- **Price:** Bought 100 sh @ ₱7.95 + 600 sh @ ₱7.93 = 700 sh total,
  real weighted avg cost ₱7.9329/sh (₱5,553 total). Both fills landed
  inside the stated ₱7.86–8.02 entry zone.
- **Setup at the time:** The weakest fundamental story of today's
  three fills (Q1 NI -2% YoY, FY25 NI -21%, fair value already cut
  ₱10.04→9.42) — a speculative bottom-fish tier, not a clean trend
  pullback like OGP. Stop ~₱7.57–7.67, giving ~3.3-4.6% cushion —
  tighter than OGP's but still a legitimate in-zone fill, not a
  thin-margin entry like today's ICT fill.
- **What actually happened:** Filled as the stock continued fading
  from Wednesday's +6.62% intraday peak, right down into the stated
  zone — a real pullback into the zone, not a chase.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.**
- **Lesson: N/A yet.**

### 2026-09-18 — OGP — Entry filled, clean zone fill
- **Price:** Bought 100 sh @ ₱36.65 (real fill). Cost basis ₱3,665
  total. Filled right at the top boundary of the stated ₱34.20–36.65
  entry zone — a standard, well-fitting fill, unlike the same-day ICT
  entry logged below (which landed at the old stop level instead).
- **Setup at the time:** Real catalyst on file: Didipio mine life
  extended to 2037, $1.958B long-term investment confirmed, solid
  2026 production guidance. Stop ~₱32.60–33.15, giving real room
  (~9.5-11.0% cushion) — a healthy, normal setup compared to today's
  other fill.
- **What actually happened:** Filled cleanly inside the zone. Not yet
  resolved.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.**
- **Lesson: N/A yet — but worth noting as a contrast: this is what a
  standard staged-pullback entry looks like on this account, versus
  the same-day ICT fill which deviated from that pattern. Useful
  side-by-side reference for future entries.**

### 2026-09-18 — ICT — Entry filled, at the old stop level not the entry zone
- **Price:** Bought 10 sh @ ₱915 (real fill). Cost basis ₱9,150 total.
- **Setup at the time:** ICT's stated entry zone was ₱947–962 (a
  pullback zone), with a stop at ~₱900–915 below that. Today's price
  action pulled back further than the zone — down to ₱913.00 intraday
  (-2.35%) — and the fill (₱915) landed right at the TOP of what was
  originally defined as the *stop-loss* range, not inside the entry
  zone. Flagged this directly before logging: using the existing
  ₱900–915 stop as-is gives a cushion of only ~0-1.6%, far thinner
  than any other position on this account. Asked explicitly how to
  handle the stop — **user chose to keep ₱900–915 as-is**, accepting
  the thin cushion rather than deriving a fresh stop below ₱915.
- **What actually happened:** A real fill, but structurally different
  from every other entry logged this session — those all landed
  inside or just below their stated entry zones with real room to a
  stop well below. This one landed at the boundary of the stop
  itself. The underlying catalyst (US government 10% stake, Nvidia
  $5B co-investment, Apple chip partnership) is real and among the
  strongest reviewed on this list, but the entry timing doesn't match
  this account's usual staged-pullback discipline.
- **Plan adherence: N/A** — this wasn't a pre-committed staged entry
  being executed; it was a live decision made outside the account's
  existing zone framework. Not graded as Yes/No since there was no
  prior plan for this specific fill to adhere to or deviate from.
- **Lesson: N/A yet — but worth tracking closely.** With ~0-1.6%
  cushion to the stop, this position has essentially no room for
  normal daily noise before triggering. If it survives past the next
  session or two, that's meaningful information about whether ₱913-915
  is turning into real support; if it doesn't, the thin-cushion choice
  will be the direct, named cause, not a mystery.

### 2026-09-17 — SCC — Final exit (position fully closed)
- **Price:** Sold the remaining 400 sh @ ₱20.05 (real fill). Cost
  basis ₱37.7423/sh (real avg). Realized loss on this final tranche ≈
  **-₱7,076.92 gross** ((20.05 - 37.7423) × 400). SCC is now fully
  closed — no shares remain.
- **Setup at the time:** Same real bounce already logged in the
  09-17 partial-take entry below (+14.37%→+23.05% intraday off a
  genuinely bad fresh headline — DOE scrapping the 2026 coal auction
  round to force a rebid, not an automatic re-award). Price had pulled
  back slightly from the session high (₱21.10) by the time of the
  earlier 400-sh trim (₱20.25), and continued drifting down toward the
  close.
- **What actually happened:** the stated plan, set earlier the same
  day, was to revisit the last 400 sh **tomorrow** (2026-09-18) based
  on whether the move continued. Instead, the user sold the remainder
  today, same session, at ₱20.05 — a lower price than the earlier
  400-sh trim (₱20.25), meaning waiting even the rest of today did not
  pay off. This is a real, worth-naming deviation from the stated
  plan, not a technicality: "revisit tomorrow" and "sold today" are
  different decisions, and the second one happened without an
  explicit check-in on why the plan changed.
- **Plan adherence: NO** — the specific stated plan (wait until
  tomorrow) was not followed. Worth being honest rather than
  reframing this as a good outcome after the fact: the final fill
  (₱20.05) was worse than the price available when the "wait until
  tomorrow" plan was set (₱20.25 was the last logged price at that
  point), so this wasn't a case of the deviation paying off — the
  plan, if followed literally, could have meant selling into
  tomorrow's session at an unknown price, so it's not possible to say
  with certainty this was worse than the alternative either. What is
  certain: the decision changed same-day without being flagged as a
  revision to the stated plan at the time it changed.
- **Lesson:** SCC is now a clean, fully-closed position — total
  realized loss across all three tranches ≈ **-₱29,947.68 gross**
  (-₱15,873.84 + -₱6,996.92 + -₱7,076.92), against an original 1,600
  sh position. Worth flagging directly for the next time a multi-day
  "revisit later" plan gets set: naming explicitly, in the moment, why
  a plan is changing (not just executing the change silently) would
  make Plan adherence tracking more useful — right now this reads as
  a real gap, but the underlying instinct to lock in a real bounce on
  a name with no stop and a large embedded loss is not unreasonable on
  its own terms.

### 2026-09-17 — SCC — Partial take (second trim, 50% of the remainder, into a real bounce)
- **Price:** Sold 400 sh @ ₱20.25 (real fill), out of the 800 sh
  remaining after the 2026-09-11 trim. Cost basis unchanged at
  ₱37.7423/sh (real avg). Realized loss on this trim ≈ **-₱6,996.92
  gross** ((20.25 - 37.7423) × 400). 400 sh still open.
- **Setup at the time:** SCC spiked as much as +23.05% intraday
  (₱16.74→₱20.55→a session high of ₱21.10) on genuinely large volume
  (16.9M+ shares, ₱338M+ traded) — despite a fresh, bad headline the
  same window (Tribune, Sept 16: DOE scrapped the 2026 coal auction
  round specifically to force Semirara into a rebid rather than an
  automatic re-award). Read at the time: most likely a technical
  mean-reversion bounce off a deeply oversold weekly RSI (28.00,
  flagged 2026-09-10), not the market pricing in good news. The
  underlying long-term downtrend and contract-loss risk were assessed
  as unchanged by the bounce.
- **What actually happened:** the user's stated plan (given ~1 hour
  earlier) was to wait for the actual 3:00 PM close and decide on the
  full remaining 800 sh based on whether it held. Instead, a partial
  exit was taken ahead of the close, on half the remainder, while the
  bounce was still live (₱20.25, close to but off the ₱21.10 high) —
  a real-time judgment call to lock in part of the recovery rather
  than risk the full remainder into an unresolved close. This is a
  deviation from the stated plan's mechanics (wait for close, all-or-
  nothing), but not necessarily a bad outcome — taking a partial gain
  on a name still down ~46% overall is a reasonable risk-management
  move even if it didn't literally match the plan as stated.
- **Plan adherence: PARTIAL** — the underlying goal (don't let a real
  bounce on a no-stop position go unmanaged) was honored, but the
  specific mechanism stated ("wait for close, then decide on all 800
  sh") wasn't what actually happened. Worth naming honestly rather
  than forcing a clean Yes/No: this reads more like an improvised,
  reasonable adjustment mid-plan than either full adherence or a
  discipline lapse.
- **Lesson:** SCC still has no stop on the remaining 400 sh — this
  trim reduced exposure but didn't resolve that standing gap. Also
  worth revisiting explicitly: when a stated plan is "wait for X, then
  decide," a mid-course partial action is a legitimate third option
  worth naming as such going forward, rather than the two originally
  framed as if they were the only ones (hold to close vs. exit now).

### 2026-09-16 — BLOOM — Stop-out (RESOLVED — second successful execution, same day as BPI)
- **Price:** Sold 1,000 sh @ ₱2.08. Stated stop range was ₱2.05–2.10;
  the fill landed just below it, consistent with a market order during
  a fast-moving breakdown (same pattern as BPI's fill at ₱100.90,
  just under its own stop range).
- **Setup at the time:** Starter tranche filled 2026-09-10, 1,000 sh @
  ₱2.2567 avg, inside the stated entry zone (₱2.17–2.32). Stop set at
  ₱2.05–2.10 in the same update per Portfolio Risk Rule 2. Position
  had been drifting down for several sessions with the stop gap
  narrowing each check — same slow, visible-in-advance pattern BPI
  showed before its own breach earlier the same day.
- **What actually happened:** Cost basis ₱2.2567 × 1,000 = ₱2,256.70.
  Gross proceeds ₱2.08 × 1,000 = ₱2,080.00. **Realized loss ≈ -₱176.70
  (-7.83%), gross** — before selling fees, since the exact net credit
  wasn't provided; same caveat as every other real fill logged here.
  A real, larger percentage loss than BPI's (-2.61%), consistent with
  BLOOM's higher-risk "speculative bottom-fish" tier from the start —
  the stop did its job, but a wider stop on a riskier tier costs more
  when it triggers, exactly as sized.
- **Plan adherence: ✅ YES — second same-day execution, confirms the
  pattern.** BPI and BLOOM both breached their stops in the same
  session (2026-09-16) and both got sold the same day. This is no
  longer a single data point — it's now two consecutive real tests,
  both passed, directly following the 2026-09-14/15 discipline
  conversation. Worth naming plainly: this is real, demonstrated
  behavior change, not a hoped-for intention.
- **Lesson:** (1) Two stops breaking the same session is exactly the
  stress-test noted as pending in the earlier version of this entry —
  it held. (2) BLOOM's larger percentage loss vs. BPI's is a direct,
  visible consequence of its wider, riskier-tier stop (₱2.05–2.10 is
  proportionally further from entry than BPI's ₱101.00–101.50 was) —
  the sizing math worked as designed, not a surprise. (3) Two clean
  executions in one day is a real pattern now, not a fluke — worth
  checking again after the next few tests whether it holds, rather
  than declaring the discipline problem solved off two data points.

### 2026-09-16 — BPI — Stop-out (RESOLVED — stop executed as planned)
- **Price:** Sold 20 sh @ ₱100.90, market order. Stated stop range was
  ₱101.00–101.50; day's low was ₱100.90 — the fill landed right at
  that low, consistent with a market order during a fast-moving
  breakdown rather than getting the top of the stop range.
- **Setup at the time:** Starter tranche filled 2026-09-10/11 at
  ₱103.6050 avg (20 sh, 2 board lots), inside the stated entry zone.
  Stop set at ₱101.00–101.50 in the same update per Portfolio Risk
  Rule 2. Price spent three full sessions (2026-09-14 through 09-16)
  grinding closer to this level — never a sudden gap, a slow, visible
  approach that gave real advance warning each time "positions" was
  checked, then broke through on 09-16.
- **What actually happened:** Cost basis ₱103.6050 × 20 = ₱2,072.10.
  Gross proceeds ₱100.90 × 20 = ₱2,018.00. **Realized loss ≈ -₱54.10
  (-2.61%), gross — figures before selling fees**, since the exact net
  credit wasn't provided; ask for it if precision matters here, same
  caveat as the LTG/SCC entries above. A small, contained loss — the
  stop did exactly what a stop is for: capped what could have kept
  compounding into something much larger (NIKL fell -9.92% the same
  session; BPI's own loss stayed under 3%).
- **Plan adherence: ✅ YES — the first real, live stop test on the PSE
  side of this project, executed cleanly.** This directly follows the
  2026-09-14/15 discipline conversation (loss-aversion, "i don't
  follow trading plans consistently," the NVDA gap that prompted it)
  and the plan-adherence tracking field added specifically to catch
  this. Worth stating plainly: the follow-through happened. This is
  real evidence to weigh against the NVDA miss, not just a hoped-for
  intention — see the LTG/SCC "Plan adherence: Yes" backfills for the
  broader pattern this fits into.
- **Lesson:** (1) The alerting discipline this project built — three
  sessions of visible, narrowing warning via "positions"/"summary,"
  then a capitalized flag the moment the level actually broke — worked
  exactly as designed and led directly to the correct action, not just
  awareness of the problem. (2) A small, early, disciplined loss (2.61%
  gross) is the entire point of having a stop — the alternative
  (NIKL's -9.92% same-session move, still held) shows what an
  unstopped position can do in a genuinely bad broad-market session.
  (3) This name is now free of the concentration/stop-proximity
  concern it carried for a week — one fewer thing to actively monitor.

### 2026-09-10 — LTG — Partial take (30% at +20% rule)
- **Price:** ₱14.98 at the time of this conversation (position was
  already up 33.59% when reported, cost basis ₱11.21 implied)
- **Setup at the time:** Not a `WATCHLIST.md` staged entry — a
  pre-existing holding, entered before this project's discipline
  existed. Weekly chart shows a genuine multi-year recovery uptrend
  (from ~₱8-9 in 2022-23 back to testing 2021 highs), not chop — that
  read only became clear once the weekly chart was actually pasted;
  the daily-only view alone read as range-bound and would have
  supported a tighter, more conservative trail.
- **What actually happened:** The user's own standing rule (sell 30%
  once unrealized profit exceeds +20%) had already been applied before
  this was even discussed — a real, working discipline independent of
  this project's chart-reading framework.
- **Plan adherence: Yes** — worth noting explicitly (backfilled
  2026-09-15) since this is a real, positive precedent: the rule was
  followed *proactively*, without prompting, before this project even
  formalized it in writing. Good evidence this isn't someone
  constitutionally unable to execute a plan — the gap that later
  showed up on NVDA is specific, not universal.
- **Lesson:** (1) The daily-only chart materially understated this
  setup's quality — always get the weekly before concluding "no
  conviction" on a name that's been held a while, not just on new
  watchlist candidates. (2) The partial-take-at-+20% rule is now
  formalized in `WATCHLIST.md`'s Exit methodology for all future
  trades, not just this one — worth tracking whether it consistently
  improves outcomes vs. either an all-at-once exit or a pure trailing
  stop with no partial take.

### 2026-09-10 — APX — Target hit (T1 + old T2, new 52w high)
- **Price:** T1 (₱17.50-17.66) and old T2 (₱18.46, then-52w-high) both
  achieved; new 52-week high of ₱19.18 made intraday, same session.
- **Setup at the time:** Trend pullback/continuation tier, reviewed
  2026-09-09 at ₱16.80 after a distribution/rejection candle — flagged
  with real caution ("wait for the next 1-2 sessions to see where it
  actually stabilizes"). Entry never actually triggered a full staged
  fill in this journal's tracked sense — this documents the setup
  running to target, not a confirmed user position.
- **What actually happened:** The caution about the distribution
  candle didn't play out as a further breakdown — price stabilized and
  resumed the uptrend within a day, hitting both profit targets and a
  fresh 52-week high. The original T2 (set at the then-current 52w
  high) became stale the moment price broke through it, with no target
  defined above — had to be patched reactively (R-multiple stretch
  target added 2026-09-10) rather than planned for.
- **Lesson:** (1) A single rejection/distribution candle in an
  otherwise-clean uptrend doesn't reliably predict a deeper pullback —
  worth weighing that caution a bit less heavily next time a similar
  candle shows up in a name with no other bearish evidence (RSI/MACD
  both still fine). (2) **Process fix, not just an observation**: any
  future T2 set at "the current 52-week high" should note upfront that
  it's a moving target that will need redefining if broken, rather
  than treating a fresh 52w high as an unlikely edge case each time.

### 2026-09-11 — SCC — Partial take (portfolio-concentration trim, 50%)
- **Price:** ₱17.90 (user-reported real fill)
- **Setup at the time:** Not a chart-driven exit — a portfolio-risk
  trim decided 2026-09-10 after SCC was found at 61.4% of current
  portfolio value with no stop or decision framework on file (see
  Portfolio Risk Rules, Rule 1). SCC's own technical/fundamental case
  was mixed-to-bad throughout (weekly downtrend, COC No. 5 coal-block
  auction risk, no 2026 dividend) — this trim wasn't a "the setup
  worked" exit, it was a position-sizing correction independent of
  the chart.
- **What actually happened:** Sold 800 of 1,600 shares @ ₱17.90.
  Against the real average cost basis (₱37.7423/share): gross proceeds
  ₱14,320.00, cost basis of the sold shares ₱30,193.84, **realized
  loss ≈ -₱15,873.84 (-52.57%)** — figures are gross, before selling
  fees (broker commission + PSE/SCCP/SEC charges), since the exact net
  fill wasn't provided; ask for the real net proceeds if precision
  matters here, same caveat as the LTG partial-take estimate above.
  Remaining 800 shares keep the same ₱37.7423 cost basis, still
  showing roughly the same -52.6% unrealized loss — this trim reduced
  *exposure*, it didn't change the *per-share* loss, which is still
  fully live on the remaining half.
- **Plan adherence: Yes** (backfilled 2026-09-15) — the trim was
  discussed and decided 2026-09-10, executed 2026-09-11. This one is
  genuinely the harder case to execute, not the easier one: a real,
  large, realized loss on a deeply underwater position is exactly the
  kind of decision loss-aversion fights hardest against — and it still
  got done. Worth remembering this alongside the NVDA gap, not just
  the miss.
- **Lesson:** (1) This confirms the trader-not-investor / trim
  discipline can actually be executed on a real, large, deeply
  underwater position — not just a plan on paper. (2) A concentration
  trim and a "the thesis is wrong, exit fully" decision are different
  actions — this was explicitly the former; SCC's underlying
  auction-risk thesis is unresolved and remains a real reason to
  revisit the *remaining* 800 shares, not something this trim settled.
  (3) Realized loss booked here is real capital, not paper — worth
  weighing against what redeploying that ₱14,320 (gross) into a
  higher-conviction name from the Summary table could earn back, since
  the point of trading (not investing) this account is compounding
  the capital that's freed up, not just reducing the loss's visibility.

### 2026-09-10 — DMC — Data-quality correction (daily indicators)
- **Price:** ₱7.97 (both chart pastes, same day)
- **Setup at the time:** Speculative bottom-fish tier, reviewed earlier
  the same day at ₱7.97 — first chart read as still below every MA,
  RSI oversold (32.18 daily). A confirmation trigger was set using a
  daily EMA10 of "9.26."
- **What actually happened:** A second, ATR-added paste of the same
  stock (same day) showed daily MA20/EMA10 both at 7.87 and RSI 58.14
  — nothing like the first read. Weekly RSI matched exactly both times
  (40.30), which pinpointed the problem: only the *daily* panel was
  wrong, almost certainly because that first chart's cursor was
  resting on a stale "29 May" hover position (already suspected for
  its price readout, now confirmed to have corrupted the whole
  indicator panel, not just the price line). Under the corrected
  numbers, price was already above both daily EMA10 and MA20 the whole
  time — the Confirmation-add trigger was likely satisfiable same-day,
  not "~15-18% away" as first recorded.
- **Lesson:** A chart screenshot's own on-screen indicator panel can be
  silently wrong if the cursor is resting on a historical point rather
  than the live bar — not just the top OHLC/price readout, which was
  the only thing flagged as at-risk before. Cross-checking a
  slower-moving reference (like weekly RSI, which shouldn't change
  chart-to-chart on the same day) is a cheap, effective way to catch
  this kind of corruption. Worth a standing habit: when two figures
  from the same underlying stock disagree sharply within one session,
  check whether one of them could be a stale-cursor artifact before
  assuming the market actually moved that much.

---

## Pending — outcomes not yet known

*(Trades with a plan on file but no resolution yet — move each to the
Log above once it actually resolves, don't pre-judge here.)*

- **BLOOM — Starter FILLED, 2026-09-10.** 1,000 shares @ ₱2.2567 avg
  (incl. fees), raw price ₱2.24, real cost ₱2,256.70 — close to but
  slightly better than the ~₱2,300 estimate. Confirmation-add still
  pending (next candle no fresh low, or close back above ₱2.34 EMA10).
  Not yet a resolved outcome — move to the Log once the position
  closes or the confirmation add fires.
- **BPI — Starter FILLED, 2026-09-10.** 20 shares (2 board lots) @
  ₱103.6050 avg (incl. fees) — real cost ₱2,072.10, higher than the
  ~₱1,060 (1-lot) estimate because the user bought 2 lots, not 1.
  Confirmation-add still pending (next candle no fresh low, or close
  back above EMA10 104.63/VWAP 104.33). Real capital deployed so far:
  BLOOM ₱2,256.70 + BPI ₱2,072.10 = ₱4,328.80, cash on hand ₱4,353.23
  per user (implies actual starting capital ~₱8,682, not exactly the
  ₱8,000 planning estimate).
- **DMC** — live weekly-MA20 test as of 2026-09-10, confirmation
  trigger likely already satisfied on the daily timeframe (see the
  data-quality correction entry above) — awaiting the weekly close for
  full confirmation.
- **NIKL — Starter FILLED, 2026-09-11.** 1,000 shares @ ₱4.6738 avg,
  real cost ₱4,673.80 — landed in the shallow starter zone
  (₱4.60–4.70) on the first real pullback since this name was added.
  Stop ₱3.90–3.95 active immediately. **First position opened under
  the T1-full-exit rule** — no partial take planned at T1 (₱5.20–5.40),
  a full exit instead; move to the Log once that resolves one way or
  the other. Real cash on hand after this fill and the same-day SCC
  trim: ₱13,942 (user-reported) — see Capital tracking in
  `WATCHLIST.md` for the reconciliation against the estimated figure.
