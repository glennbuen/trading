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
| Real closed-position events | 1 (NVDA stop-out, 2026-09-16) |
| Process-correction events | 1 (NVDA stop-discipline gap, 2026-09-14/15 — not a P&L event, a process lesson) |
| Realized P&L | **-$0.44 gross (NVDA)** — trivial in dollar terms, real as a first data point |
| Win rate / avg R-multiple | Not yet meaningful — 1 closed trade, a loss |
| **Plan adherence rate** | **1/2 — mixed record, stated plainly.** The original 30-min post-open plan (2026-09-14/15) was NOT followed. The eventual close (2026-09-16) DID happen, just delayed — logged separately as "partial" adherence, not full credit. Compare to PSE's BPI stop-out the same day, which executed same-session and is the cleaner example. Too small a sample to mean anything statistically yet. |

---

## Log

### 2026-09-16 — AMZN — Entry filled, immediately testing its stop
- **Price:** Bought 0.05 fractional sh @ $252.72 ($12.64 total) — below
  the stated entry zone ($255-259), a better fill than planned, same
  pattern as the original NVDA/INTC fills. **Current price ($248.42,
  -1.93% same-day check) is already INSIDE the stated stop range
  ($246-249)** — the position is being tested within days of filling,
  during the same broad correlated selloff that just took out two PSE
  stops (BPI, BLOOM) the same week.
- **Setup at the time:** Real Q3 2026 guidance, Strong Buy consensus,
  daily+weekly confluence entry — the setup itself hasn't changed.
  What's changed is timing: this filled into an already-weak, broadly
  correlated market stretch (see the 2026-09-16 conversation on
  whether entries needed adjusting — conclusion was no, the stops are
  sized correctly, but new entries into this stretch carry real
  correlated risk).
- **What actually happened:** No resolution yet — **this entry is
  being logged as a live flag, same convention as the BPI/BLOOM
  breach entries before they were resolved.** No automated stop exists
  on this fractional position; a manual decision is needed if it goes
  further.
- **Plan adherence: N/A yet — nothing to adhere to until the stop is
  actually tested further or the position resolves.** Worth watching
  given the two same-day executions on BPI/BLOOM just demonstrated the
  discipline holding — this is the next real test if $246-249 breaks.
- **Lesson (partial, pending resolution):** A genuinely good entry
  (better price than planned) can still end up under immediate
  pressure if it fills during a correlated risk-off stretch — the
  entry price being favorable doesn't insulate against the broader
  market conditions that are already in motion. Update this entry with
  the actual resolution once known.

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
