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
| Real closed-position events | 3 (NVDA stop-out, AMZN stop-out — both 2026-09-16; INTC T1 exit 2026-09-23) |
| Process-correction events | 1 (NVDA stop-discipline gap, 2026-09-14/15 — not a P&L event, a process lesson) |
| Realized P&L | **-$0.44 gross (NVDA) + -$0.23 gross (AMZN) + +$3.01 gross (INTC) ≈ +$2.34 net** — first real winner in the closed-position log |
| Win rate / avg R-multiple | 1-for-3 (INTC the only win so far) — still too small a sample to mean anything statistically |
| **Plan adherence rate** | **3/4 events, improving but not clean.** NVDA's original 30-min plan (2026-09-14/15) was NOT followed, only resolved late. AMZN's stop (2026-09-16) WAS executed within the stop range, no hesitation. INTC's T1 exit (2026-09-23) WAS a full, correct exit — but placed two sessions after the T1 signal first fired, a smaller echo of the same lag pattern as NVDA's gap, just with a favorable outcome this time rather than a costly one. |

---

## Log

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
