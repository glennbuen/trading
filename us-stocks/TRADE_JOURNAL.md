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
- **Lesson:** (repeat, adjust, or confirm/contradict the methodology)
```

Keep entries honest — a lesson from a loss is as valuable as one from
a win, and a win for the wrong reason (right result, flawed process)
is worth flagging too.

## Performance Summary (rolled up from the Log, refresh periodically)

| Metric | Value |
|---|---|
| Real closed-position events | 0 |
| Process-correction events | 1 (NVDA stop-discipline gap, 2026-09-14/15 — not a P&L event, a process lesson) |
| Realized P&L | $0 |
| Win rate / avg R-multiple | Not yet meaningful — no trades closed |

---

## Log

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
