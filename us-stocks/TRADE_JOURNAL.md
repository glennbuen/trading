# US Stocks Trade Journal — Wins, Losses, and What They Taught

A record of what actually happened after each trade action (entry,
partial take, stop-out, target hit, exit) — not just the plan, but the
outcome and the lesson. Companion to `WATCHLIST.md`. Ported structure
from `pse/TRADE_JOURNAL.md` — same discipline, new market.

## How to log an entry

```
### YYYY-MM-DD — SYMBOL — ACTION (Entry / Partial take / Stop-out / Target hit / Exit)
- **Price:** $X.XX
- **Setup at the time:** (tier, play type, what the read was)
- **What actually happened:** (thesis play out as expected? stopped on
  noise or a real break? ran past target?)
- **Plan adherence:** Yes / No — did the exit actually execute at the
  pre-committed level? If No, what happened in the moment (the real
  thought, not a retroactively tidied-up version) and how long the gap
  was between "price hit the level" and "order actually placed" (or
  "never placed"). This is a separate score from win/loss — a trade
  can be a win with No adherence (got lucky waiting) or a loss with
  Yes adherence (the plan was followed and still lost, which is a
  healthy, expected outcome of a probabilistic system, not a failure).
- **Lesson:** (repeat, adjust, or confirm/contradict the methodology)
```

**Added 2026-09-15, prompted by a real discipline gap on NVDA** (see
Log below): win/loss tracks whether the *market* cooperated.
Plan-adherence tracks whether *you* did. Conflating them hides the
real problem — a trader can look "fine" on P&L for a long stretch
while quietly never executing an exit on time, and only find out when
a big one goes against them. Log this field honestly every time, not
just when it's flattering.

Keep entries honest — a lesson from a loss is as valuable as one from
a win, and a win for the wrong reason (right result, flawed process)
is worth flagging too.

## Performance Summary (rolled up from the Log, refresh periodically)

| Metric | Value |
|---|---|
| Real closed-position events | 7 (NVDA stop-out, AMZN stop-out — both 2026-09-16; INTC T1 exit 2026-09-23; PLTR T1 exit 2026-10-13; MSFT T1 exit, NBIS stop-out, HOOD stop-out — all 2026-10-15) |
| Process-correction events | 1 (NVDA stop-discipline gap, 2026-09-14/15 — not a P&L event, a process lesson) |
| Realized P&L | **-$0.44 gross (NVDA) + -$0.23 gross (AMZN) + +$3.01 gross (INTC) + +$2.74 gross (PLTR) + +$1.43 gross (MSFT) + -$1.36 gross (NBIS) + -$0.96 gross (HOOD) ≈ +$4.19 net** — three real winners, two of them T1 exits |
| Win rate / avg R-multiple | 3-for-7 (INTC, PLTR, MSFT wins) — small sample, but both T1-only exits taken so far (INTC, PLTR) plus MSFT have all been clean |
| **Plan adherence rate** | **6/8 events, improving.** NVDA's original 30-min plan (2026-09-14/15) was NOT followed, only resolved late. AMZN's stop (2026-09-16) WAS executed within the stop range, no hesitation. INTC's T1 exit (2026-09-23) WAS a full, correct exit, placed two sessions after the signal fired. PLTR's T1 exit (2026-10-13) WAS also full and correct, decided the same day the signal fired. MSFT's T1 exit (2026-10-15) WAS full and correct, sold inside the stated zone. NBIS's stop-out (2026-10-15) was followed through on intent, but the fill landed below the stated $196-205 stop zone — a real execution gap. HOOD's stop-out (2026-10-15) was the same shape — intent followed through, but the fill landed below the $99-102 stop zone too, the second gap-through in two days. |

---

## Log

### 2026-10-15 — TSM — Entry filled, below the zone after a gap-through
- **Price:** Bought 0.06 fractional sh @ $411.35 ($24.68 total) —
  below the stated entry zone ($420-425), filled after price gapped
  through the zone on today's open rather than giving a clean zone
  touch. Stop ~$403-409 active immediately per Portfolio Risk Rule 2.
  Real stop gap at this fill is only ~0.6-2.0%, much tighter than the
  ~3.8-4.0% the original zone-based position sizing assumed.
- **Setup at the time:** Real, consistent growth story on file (Aug
  revenue +53.3% YoY, Q2 2026 revenue +36%/net income +77.4% YoY).
  TSMC actually reported Q3 2026 revenue above the high end of
  guidance the same morning — a genuinely positive catalyst — but the
  stock dropped anyway, as part of the broad selloff that also hit
  META/AMD/MRVL/HOOD/NBIS this stretch, not on the earnings itself.
- **What actually happened:** Filled during the same broad selloff
  that produced the NBIS and HOOD stop gap-throughs the day before and
  that same morning — this time on the buy side, catching a price that
  had already moved past the intended zone rather than waiting for a
  clean touch.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.** Worth flagging now rather than at resolution: this is
  the second entry on this account that didn't fill inside its stated
  zone (NBIS was the first, 2026-09-16), and this one fills with a
  meaningfully tighter stop gap than planned as a direct result.
- **Lesson: N/A yet — but the tight stop gap (~0.6-2.0%) means normal
  daily noise has a real chance of triggering it quickly. Worth
  watching whether a fill this close to the stop behaves differently
  than a standard zone entry once this resolves, same open question
  flagged on NBIS's original entry.**

### 2026-10-15 — HOOD — Stop-out (RESOLVED)
- **Price:** Sold 0.1 fractional sh @ $96.33 ($9.633 total). Cost basis
  was $105.96 (0.1 sh, $10.596 total, filled 2026-09-16). Realized
  loss ≈ -$0.96 gross, -9.09%.
- **Setup at the time:** Real, two-sided story on file — a genuine 32%
  YTD decline earlier in 2026 balanced against August platform assets
  hitting $384B (+26%) and two analyst target raises. Stop was set at
  $99-102 (1-1.5x daily ATR below the zone), the tightest stop gap of
  any position on this account at entry (~3.3%).
- **What actually happened:** The broad market selloff that started
  2026-10-14 (TSM/META/AMD/MRVL all down 3-9% that session) continued
  into 2026-10-15's open — HOOD closed 2026-10-14 at $101.08, already
  inside the stop zone, then gapped further down at today's open to
  $96.21 before the sell was placed at $96.33, **below the stated
  $99-102 stop zone entirely.** Same shape as NBIS's exit the day
  before.
- **Plan adherence: ✅ YES on following through on the decision to
  sell, but with the same execution gap flagged on NBIS** — the stop
  zone was never going to be defended by a resting order (no automated
  stops on Webull SG fractional shares), so once price gapped through
  it overnight/pre-market, the eventual fill landed well past the
  planned level. This is now the second such gap in two days.
- **Lesson:** two gap-throughs in a row (NBIS, HOOD) during the same
  broad selloff stretch is worth naming as a pattern, not two isolated
  incidents — manual stops on this account are vulnerable to exactly
  this failure mode during a fast, correlated market move, independent
  of how promptly the decision to sell is made. Worth discussing
  whether tighter-stop names (HOOD's ~3.3% original gap, same category
  as NBIS's ~4.2%) need a different handling approach during
  broad-selloff conditions specifically, since both gap-throughs
  happened during the same market event.

### 2026-10-15 — MSFT — Target hit (T1 full exit, RESOLVED)
- **Price:** Sold 0.03 fractional sh @ $541.59 ($16.2477 total). Cost
  basis was $493.81 (0.03 sh, $14.8143 total, filled 2026-09-21).
  Realized gain ≈ +$1.43 gross, +9.68%.
- **Setup at the time:** Azure growth hit 43% with annualized revenue
  above $100B, backlog surged 84% to $678B, first-time separate Azure
  revenue disclosure. Analysts raised the target to $600 from $500. T1
  was set at $540-554 (52w-high retest) per this account's T1-only
  full-exit rule.
- **What actually happened:** Price closed inside the $540-554 T1 zone
  for two straight confirmed-close sessions (2026-10-12 at $543.45,
  2026-10-13 at $541.59 pre-exit) — flagged both times as a real,
  unactioned decision point, same situation as INTC and PLTR before
  their exits. The exit was placed 2026-10-15 at $541.59, inside the
  stated T1 range.
- **Plan adherence: ✅ YES** — a full T1 exit, not a partial trim, sold
  within the stated zone. Same pattern as INTC and PLTR: the signal
  sat flagged for more than one session before the actual sell was
  placed, but the position was closed cleanly once acted on, not held
  past the zone.
- **Lesson:** the third T1-only full exit in the log, and the third
  real winner off this specific rule. Three clean executions now (INTC,
  PLTR, MSFT) — the pattern is holding up, still a small sample but
  consistent: full exit, no partial-hold rationalization, every time.

### 2026-10-15 — NBIS — Stop-out (RESOLVED)
- **Price:** Sold 0.05 fractional sh @ $187.00 ($9.35 total). Cost
  basis was $214.20 (0.05 sh, $10.71 total, filled 2026-09-16).
  Realized loss ≈ -$1.36 gross, -12.70%.
- **Setup at the time:** Fresh catalyst on file (Palantir named Nebius
  its preferred sovereign AI infrastructure partner, Sept 8, 2026).
  Stop was set at $196-205 (1-1.5x daily ATR below the zone). The
  position had already tested the bottom of that zone once
  (2026-10-13, intraday low $198.77) and recovered.
- **What actually happened:** The user stated intent to sell NBIS
  (along with MSFT) a session ahead of the actual exit. By the time the
  sell was placed, price had moved well below the stated $196-205 stop
  zone, filling at $187 — **a real gap-through, not a clean execution
  at the planned level.** Worth naming plainly rather than treating
  this as a standard in-zone stop: the realized loss (-12.70%) is
  meaningfully worse than a fill at the top of the stop zone
  (-4.3%) or even the bottom of it (-8.6%) would have been.
- **Plan adherence: ✅ YES on following through on the decision to
  exit, but with a real execution gap worth flagging** — the intent to
  sell was declared and acted on, same as MSFT, but unlike MSFT's
  clean in-zone fill, NBIS's actual price landed outside the planned
  stop range entirely. This is a sourcing/timing gap (price moved
  between when the stop was last confirmed and when the order was
  placed), not a process failure of the same kind as NVDA's 2026-09-15
  discipline gap — the decision was made and executed — but it's a
  reminder that a stated stop zone is not a guarantee of the fill
  price once the order is actually placed, especially on a thin
  fractional position with no resting stop order on Webull SG.
- **Lesson:** second loss on this account, following NVDA and AMZN.
  Combined with those, reinforces that stops on this account are
  manual, not automated — the gap between "price is near the stop" and
  "the sell is actually placed" is where real slippage can happen, on
  top of the normal probabilistic loss a stop is supposed to produce.

### 2026-10-13 — PLTR — Target hit (T1 full exit, RESOLVED)
- **Price:** Sold 0.07 fractional sh @ $210.2166 ($14.72 total,
  corrected 2026-10-14 to the exact fill — originally logged at a
  rounded $210.00). Cost basis was $171.13 (0.07 sh, $11.98 total,
  filled 2026-09-16). Realized gain ≈ +$2.74 gross, +22.84%.
- **Setup at the time:** Fresh, convergent catalyst — three analyst
  firms (UBS, Phillip Securities, DA Davidson) raised targets within
  days of each other citing real demand momentum, $3.4B Q2 bookings,
  and 157% net dollar retention. T1 was set at $205-208 (52w-high
  retest) per this account's T1-only full-exit rule.
- **What actually happened:** Price cleared T1 on 2026-10-09 (closed
  $209.05, above the entire range). The user stated intent to close
  the position on Monday (2026-10-12) the same day T1 cleared — ahead
  of the actual exit, not after it. The sale itself landed 2026-10-13
  at $210.2166, inside the range the stock had been trading since
  clearing T1.
- **Plan adherence: ✅ YES, and a cleaner example than INTC's** — the
  T1 signal fired and the stated intent to exit was declared the same
  day, not two sessions later. The actual fill came slightly after
  the stated "Monday" target, but the decision itself was made
  immediately upon the signal firing, which is the more important
  half of plan adherence — deciding promptly, even if the mechanical
  execution landed a session later.
- **Lesson:** this is the second T1-only full exit in the log (INTC
  being the first) and the second real winner. Combined with INTC,
  the T1-only rule now has two clean executions behind it — both
  real gains, both full exits with no partial-hold rationalization.
  Worth noting as the pattern solidifying, though still early (2
  data points) to call it proven.

### 2026-09-23 — INTC — Target hit (T1 full exit, RESOLVED)
- **Price:** Sold 0.15 fractional sh @ $121.69 ($18.2535 total). Cost
  basis was $101.6173 (0.15 sh, $15.24 total, filled 2026-09-11).
  Realized gain ≈ +$3.01 gross, +19.76%.
- **Setup at the time:** Strongest catalyst reviewed all session — US
  government holds a 10% stake, Nvidia's $5B x86 co-development deal +
  $8.9B government investment, Apple reportedly co-designing chips
  with Intel. T1 was set at $115-120 per this account's T1-only
  full-exit rule ("trader not investor").
- **What actually happened:** Price first cleared the $115-120 T1
  range on 2026-09-21 (close $121.78, +12.14% that session) and stayed
  above it through 2026-09-22 (close $123.86). Flagged as an
  unactioned real decision point across two full refresh cycles before
  the exit was actually placed on 2026-09-23 at $121.69 — inside the
  range the stock had been trading in since clearing T1, not at a
  fresh high.
- **Plan adherence: ✅ YES, with a real gap to name honestly** — the
  T1-exit rule was followed and the position was fully closed, not
  partially trimmed or held past target. But the actual execution
  lagged the T1 signal by two sessions (T1 cleared 2026-09-21, exit
  placed 2026-09-23) — same shape as the NVDA discipline gap from
  2026-09-14/15, just smaller in magnitude and this time it worked out
  favorably (price didn't reverse below T1 during the gap). Logging
  the lag itself, not just the clean outcome, per the standing rule
  that plan-adherence tracks the honest timeline, not a tidied-up one.
- **Lesson:** the T1-only full-exit rule did its job — no partial
  hold, no "let it run further" rationalization once the decision was
  finally made. But the two-session gap between signal and execution
  is worth naming plainly: this time the stock stayed above T1 during
  the delay, so the lag cost nothing, but that's a matter of luck, not
  process. The same gap on a stock that reversed back below T1 during
  the delay would have given back real gains. Worth watching for
  whether this becomes a pattern (see NVDA's own delayed-exit history).

### 2026-09-21 — MSFT — Entry filled, exactly as planned
- **Price:** Bought 0.03 fractional sh @ $493.81 ($14.81 total). Filled
  right inside the stated $492-497 entry zone — the user explicitly
  stated the plan a session earlier ("ok target to get in msft on
  monday") and executed it almost exactly, same as WEB's pattern on
  the PSE side.
- **Setup at the time:** Real, substantive catalyst: Azure growth hit
  43% with annualized revenue above $100B, backlog surged 84% to
  $678B, first-time separate Azure revenue disclosure (a real
  transparency signal). Analysts raised the target to $600 from $500.
  Stop ~$477-482, T1 ~$540-554 (~3.6:1 R:R).
- **What actually happened:** Filled the same session a market-wide
  rally took hold (INTC +12.14%, AMD +9.95%, META +11.43% all closed
  the same day) — MSFT closed at $501.61, above the entire entry zone,
  a strong first session.
- **Plan adherence: ✅ YES** — stated the plan a session ahead, then
  executed at essentially the exact level described.
- **Lesson: N/A yet — but another clean plan-then-execute precedent,
  same pattern as WEB on the PSE side.**

### 2026-09-16 — HOOD — Entry filled, during a steep sector-correlated drop
- **Price:** Bought 0.1 fractional sh @ $105.96 ($10.60 total) — below
  the stated entry zone ($108.71-112.49), filled while HOOD was down
  sharply intraday (-4.45% by the time of the next check). Stop
  ~$99-102 active immediately per Portfolio Risk Rule 2. Stop gap only
  ~3.3% at the near bound — the tightest gap of any open position on
  this account right now.
- **Setup at the time:** Real, two-sided story on file: a genuine 32%
  YTD decline earlier in 2026 (Q1 miss, crypto revenue -47%, softening
  volumes) balanced against August platform assets hitting $384B
  (+26%) and two analyst target raises this month (Deutsche Bank to
  $138, Citizens to $165). Today's drop reads as sector-correlated —
  COIN fell on the Senate rejecting the Digital Asset Market CLARITY
  Act, and HOOD moved with it rather than on company-specific news.
- **What actually happened:** Filled into the drop rather than waiting
  for it to stabilize — same "rotate fast" pattern as this session's
  other adds, but this is now the fifth new position opened today
  (PLTR, NBIS, HOOD) or resolved (NVDA, AMZN) in a single session, on
  an account this small. Not yet resolved.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.**
- **Lesson: N/A yet — but flag now: this stop gap (~3.3%) is
  meaningfully tighter than anything else currently open on this
  account, meaning normal daily noise has a real chance of triggering
  it. Worth watching closely rather than assuming the same runway as
  NBIS/PLTR.**

### 2026-09-16 — NBIS — Entry filled, buy-the-bounce off the stop danger zone
- **Price:** Bought 0.05 fractional sh @ $214.20 ($10.71 total) — well
  BELOW the stated entry zone ($223.70-228.90), not inside it. Filled
  during a real intraday bounce, hours after the price had come within
  ~1.2% of the stop (~$196-205). Stop ~$196-205 active immediately per
  Portfolio Risk Rule 2. Current stop gap ~4.2%.
- **Setup at the time:** Fresh, credible catalyst on file (Palantir
  named Nebius its preferred sovereign AI infrastructure partner,
  Sept 8, 2026 — a specific enterprise deal). The chart context is
  different from a clean zone fill, though: this name had spent two
  days trading inside/near the zone, drifted down toward the stop, and
  today's fill is a discretionary bounce entry rather than the
  standard "price pulled back into the stated zone and held" pattern
  used for the other names on this list.
- **What actually happened:** Filled same session as the "us summary"
  refresh that had just flagged NBIS as "only ~1.2% above its stop,
  closest on the list." Not yet resolved.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.**
- **Lesson: N/A yet — but worth flagging now rather than at
  resolution: this is the first fill this session that didn't occur
  inside its originally-stated entry zone. Worth watching whether
  buy-the-bounce entries taken this close to a stop behave differently
  than standard zone fills once this resolves.**

### 2026-09-16 — PLTR — Entry filled, same-session redeploy from AMZN
- **Price:** Bought 0.07 fractional sh @ $171.13 ($11.98 total) —
  below the stated entry zone ($172.49-175.52), a better fill than
  planned, same pattern as NVDA/INTC/AMZN's original fills. Stop
  ~$161-165 active immediately per Portfolio Risk Rule 2.
- **Setup at the time:** Fresh, convergent catalyst — UBS raised its
  target $220→$250 on Sept 15 (3rd revision this year), Phillip
  Securities to $215, DA Davidson to $250, all within days of each
  other. Weekly structure genuinely clean, no overhang. T1 (full
  exit) ~$205-208, a real structural target (52w-high retest), not an
  R-multiple substitute — the strongest R:R setup (~3.5-3.7:1) added
  this week.
- **What actually happened:** Filled the same session AMZN was
  stopped out, redeploying freed-up capital into the higher-conviction
  of the two names added together (PLTR vs. HOOD) — consistent with
  this account's "rotate fast" philosophy. Not yet resolved.
- **Plan adherence: N/A yet — nothing to adhere to until this
  resolves.**
- **Lesson: N/A yet — update once this trade closes one way or the
  other.**

### 2026-09-16 — AMZN — Stop-out (RESOLVED)
- **Price:** Bought 0.05 fractional sh @ $252.72 ($12.64 total) — below
  the stated entry zone ($255-259), a better fill than planned, same
  pattern as the original NVDA/INTC fills. Sold the full 0.05 sh @
  $248.17, inside the stated stop range ($246-249).
- **Setup at the time:** Real Q3 2026 guidance, Strong Buy consensus,
  daily+weekly confluence entry — the setup itself never stopped being
  sound. What changed was timing: this filled into an already-weak,
  broadly correlated market stretch (see the 2026-09-16 conversation
  on whether entries needed adjusting — conclusion was no, the stops
  are sized correctly, but new entries into this stretch carry real
  correlated risk, exactly what played out here).
- **What actually happened:** Cost basis $252.72 × 0.05 = $12.636.
  Gross proceeds $248.17 × 0.05 = $12.4085. **Realized loss ≈ -$0.23
  (-1.80%), gross** — trivial in dollar terms given the tiny fractional
  size, same as NVDA's prior stop-out. This is the fourth stop-out
  logged this week (PSE: BPI, BLOOM; US: NVDA, now AMZN) — a genuine
  losing stretch, already discussed at length as statistically normal
  given the small resolved sample and the shared correlated market
  event behind most of them.
- **Plan adherence: ✅ YES — executed within the stop range, not held
  through it.** A genuinely good entry (better price than planned)
  still ended up under immediate pressure from broader market
  conditions already in motion — the entry price being favorable
  didn't insulate against that, and the plan was followed anyway
  rather than "waiting to see" given the favorable entry.
- **Lesson:** Confirms the pattern already logged on BPI/BLOOM/NVDA —
  a real, sound setup can still lose if it fills into a correlated
  risk-off stretch, and that's a market-timing outcome, not a flaw in
  the entry logic itself. Capital freed up and redeployed same-session
  into PLTR (see below) — consistent with this account's "rotate
  fast" exit philosophy.

### 2026-09-14/15 — NVDA — Discipline gap (stop not executed at plan trigger)
- **Price:** Stop zone $210–213. Monday 9/14 regular-session close:
  $210.96 (-3.36%), inside the zone. After-hours ticked to $212.04
  (+0.51%), still within it.
- **Setup at the time:** A broad, macro-driven selloff (Anthropic's
  Dario Amodei and OpenAI's Sam Altman both calling for slower AI
  development over the weekend) pushed NVDA's pre-market price into
  the stated stop zone. The user made an explicit, reasonable plan in
  advance: check 30 minutes after the regular open, sell if price
  hadn't recovered by then — a sensible middle ground between
  reacting to thin pre-market noise and waiting a full session.
- **What actually happened:** The plan wasn't executed. By the time
  this was revisited the next day, the confirmed close had settled
  inside the stop zone anyway (not just touched it intraday) — the
  discretionary call didn't end up mattering for the *outcome* this
  time (price hadn't sharply recovered), but the *process* gap is the
  real finding here, independent of how this particular case
  resolves. The user's own words: "i need more discipline."
- **Lesson:** This is exactly the risk the "no automated stop-loss on
  Webull SG fractional shares" warning was about — a good plan on
  paper doesn't execute itself, and the gap between "I have a rule"
  and "I followed the rule at the moment it mattered" is where real
  losses compound on a small account. Worth naming plainly rather than
  softening: the system (this file, the routine, the check-in) did its
  job — it flagged the zone breach correctly and in advance. The
  follow-through is the part that's genuinely hard and worth building
  as a practiced habit, not a one-time intention. No verdict yet on
  whether holding through this was "right" or "wrong" in hindsight —
  that depends on where NVDA goes from here — but the discipline
  question is independent of that outcome and shouldn't be graded on
  it either way.

### 2026-09-16 — NVDA — Stop-out (delayed follow-through, resolves the discipline gap above)
- **Price:** Sold 0.07 fractional sh @ $212.08. Cost basis $218.41/sh
  ($15.29 total). Realized loss ≈ -$0.44 gross (-2.88%) — trivial in
  dollar terms on a position this size, not trivial as a process data
  point.
- **Setup at the time:** Directly follows the 2026-09-14/15 discipline
  gap logged above — the 30-minute post-open plan wasn't executed,
  and the user explicitly deferred with "i'll sell later." This is
  that "later" arriving, roughly a session or two after the original
  trigger, at essentially the same price zone the stop was originally
  breached in ($212.08 vs. the $210.96–212.27 range already on
  record).
- **What actually happened:** The position got closed. Not at the
  planned moment, but it did get closed — "i'll sell later" turned out
  to be a real statement of intent, not just a way of ending the
  conversation. Worth being precise about what this does and doesn't
  redeem: it does NOT undo the process gap (the 30-minute plan still
  wasn't followed, and the delay meant riding the position through
  additional uncertainty it didn't need to sit through) — but it does
  mean the deferral wasn't indefinite avoidance, which is a real and
  different failure mode that this outcome rules out.
- **Plan adherence: PARTIAL — delayed but real.** Distinguish this
  from the PSE-side BPI stop-out logged the same day, which executed
  the same session the level broke: that one is the cleaner example
  of the discipline actually working in real time. This one is the
  more honest, mixed case — a genuine gap followed by genuine
  follow-through, not a clean pass.
- **Lesson:** A missed trigger doesn't have to become a held-forever
  position — "later" can still be a real commitment if it's actually
  kept, even imperfectly. But the better outcome is still the BPI
  pattern (same-session execution), not this one (delayed, but
  eventually done) — worth naming the difference rather than treating
  both as equivalent wins just because both closed the position
  eventually.

---

## Pending — outcomes not yet known

- **NVDA — Starter FILLED overnight, 2026-09-10/11.** 0.07 fractional
  shares @ $218.41 ($15.29) — *below* the stated entry zone
  ($220.80–223.67), a better fill than planned. First real trade on
  Webull SG, confirming fractional + limit-order mechanics worked as
  expected. Stop ~$210–213, T1 exit ~$236–240 per this account's rule.
- **INTC — Starter FILLED overnight, 2026-09-10/11.** 0.15 fractional
  shares @ $101.6173 ($15.24) — inside the stated zone ($100–106).
  Stop ~$91–94, T1 exit ~$115–120.
- Also surfaced: real starting capital is **$78.77 USD** (converted
  from S$100 at ~0.79), not the $100 USD assumed until now — corrected
  throughout `us-stocks/WATCHLIST.md`. Cash remaining after these two
  fills: **$48.24**.
