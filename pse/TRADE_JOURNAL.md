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
- **Lesson:** (what to repeat, what to adjust, what this confirms or
  contradicts about the methodology)
```

Keep entries honest — a lesson from a loss is as valuable as one from
a win, and a win for the wrong reason (right result, flawed process)
is worth flagging too, not just wins/losses at face value.

## Performance Summary (rolled up from the Log, refresh periodically)

Turns individual Log entries into aggregate numbers — win rate, average
R-multiple, total realized P&L — so the lessons compound instead of
just accumulating as isolated notes. Added 2026-09-10 per the user's
own framing of this journal as "a learning process," which needs
numbers, not just narrative, to actually measure.

**Current tally (2026-09-11) — honest about what's known vs. estimated:**

| Metric | Value | Note |
|---|---|---|
| Real closed-position events | 2 (LTG partial take, SCC partial take) | BPI/BLOOM Starters still open/unrealized |
| Setup-accuracy events (not real money) | 1 (APX target hit) | Tracked separately — confirms/disconfirms the *analysis*, not a real trade outcome |
| Process-correction events | 1 (DMC data-quality) | Not a P&L event at all — a methodology lesson |
| Realized P&L (real capital) | **~₱612 est. (LTG) + -₱15,873.84 est. (SCC) ≈ -₱15,262 net** | **Both estimated, not exact** — neither sale's real fees are captured (LTG's execution price/date wasn't recorded at the time; SCC's is gross, before selling fees). Ask the user for exact net fills if precision matters here. |
| Win rate, R-multiple average | Not yet meaningful | Sample size (2 real closed events, 1 win/1 loss) is too small — will become meaningful as BPI/BLOOM confirmations and future entries resolve |

**This section is only as good as the Log below it** — update this
table whenever a new entry is added there, not just when asked. Once
there are 5+ real closed-position events, start tracking win rate (%
of closed trades with positive realized P&L) and average R-multiple
(realized gain or loss ÷ the original risk-per-share defined at entry)
properly — not worth computing on this small a sample yet.

---

## Log

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
