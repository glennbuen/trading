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
| Real closed-position events | 2 (NVDA stop-out, AMZN stop-out — both 2026-09-16) |
| Process-correction events | 1 (NVDA stop-discipline gap, 2026-09-14/15 — not a P&L event, a process lesson) |
| Realized P&L | **-$0.44 gross (NVDA) + -$0.23 gross (AMZN) ≈ -$0.67 net** — trivial in dollar terms, a real 0-for-2 stretch as a data point |
| Win rate / avg R-multiple | Not yet meaningful — 2 closed trades, both losses |
| **Plan adherence rate** | **2/3 events, improving.** NVDA's original 30-min plan (2026-09-14/15) was NOT followed, only resolved late. AMZN's stop (2026-09-16) WAS executed within the stop range, no hesitation — same day as PSE's two clean BPI/BLOOM executions. The pattern is trending toward same-session execution, not away from it. Still too small a sample to mean anything statistically. |

---

## Log

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
