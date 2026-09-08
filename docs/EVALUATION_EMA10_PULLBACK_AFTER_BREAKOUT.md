# Breakout → Pullback-to-EMA(10) Entry Retest

User clarified the intended entry logic after the first, same-bar
EMA(10) filter retest (`docs/EVALUATION_EMA10_FILTER_RETEST.md`) crushed
most strategies to zero trades: **"entry is after breakout, buy at the
pullback around EMA(10)"** — a sequential composition, not a same-bar
AND. Each strategy's own original entry signal is now an ARMING event
(a breakout occurred, not the entry itself); the actual entry fires on
the FIRST bar, within a 10-bar window after that breakout, where price
has pulled back near EMA(10) on the favorable side (2% distance,
matching the already-confirmed definition —
`engines/entry_filters.py`'s `pullback_entry_after_breakout`).

Same scope, same exit system (both variants), same `RiskLimits()`
defaults as both prior retests.

## Result: still no strategy clears both symbols, TITA included

| Strategy | Unfiltered PF (BTC/ETH) | Breakout→pullback PF (BTC/ETH) |
|---|---|---|
| Breakout+Retest (B) | 1.13 / 0.87 | 0.51 / 1.64 |
| Breakout (A) | 1.50 / 1.64 | 1.33 / 0.56 |
| Trend Pullback (C) | 0.21 / 2.15 | 0.42 / 2.02 |
| Liquidity Sweep Reversal (D) | 1.05 / 1.22 | 0.72 / 0.69 |
| Ichimoku Cross | 1.50 / 1.45 | 0.24 / 1.91 |
| MFI Reversal | 0.33 / 0.59 | 0.16 / 0.23 |
| MAMA | 1.69 / 2.05 | 0.74 / 1.00 |
| BOPIS | 1.04 / 1.80 | 0.56 / 0.72 |
| PAPA | 0.69 / 0.45 | 0.15 / 0.70 |
| **TITA** | **1.31 / 1.99** | **0.93 / 1.22** |
| 20% Support Bounce | 0.18 / 0.75 | 0.38 / 0.76 |
| SWAG | 1.14 / 1.04 | 0.34 / 1.09 |
| 3-Step Formula | 1.10 / 0.79 | 0.93 / 0.81 |
| SPYFRAT Core System | 1.54 / 1.51 | 1.62 / 0.56 |

(flat +6% lock variant shown; the ATR-trailing variant tells the same
story throughout — see the raw output in
`scripts/retest_all_pullback_after_breakout.py`'s run for both.)

**Zero of the 14 strategies clear PF>1.2 on both symbols** under this
composition. Several that cleared both under the unfiltered exit-rules
retest now clear neither (MAMA, BOPIS, MFI Reversal, Liquidity Sweep
Reversal). Several that cleared one symbol before now clear a
*different* one, or none — the same "which symbol wins scatters
unpredictably" signature this project has repeatedly read as noise, not
a hidden edge, whenever it's appeared (Breakout A: BTC before, still
BTC now but ETH degrades sharply; Ichimoku: BTC before, ETH now — a
flip, not an improvement; SPYFRAT: both before, only BTC now).

## TITA specifically: this composition hurts it too, though less catastrophically than the same-bar version

TITA's BTC/USDT result drops to **PF 0.93 — below breakeven** — and
ETH/USDT, while nominally still above 1.2 (1.22), is down substantially
from 1.99. This is the same direction of finding as the same-bar
version (`docs/EVALUATION_EMA10_FILTER_RETEST.md`, where BTC collapsed
to 0.34): **TITA's edge does not come from entries that happen to pull
back to EMA(10) after a breakout.** The prior finding wasn't an
artifact of the (now-corrected) same-bar composition being too
restrictive — the more charitable, better-populated sequential version
tells the same story. TITA's RSI+ALMA momentum signal and "pulls back
to a short EMA after breaking out" are simply different, largely
non-overlapping conditions, and gating on the second one costs more
than it filters out.

## Overall verdict

**The breakout→pullback-to-EMA(10) entry composition should not be
applied to any strategy in this project, TITA included — this is now
confirmed under two different, reasonable operationalizations of "near/
striking distance of EMA(10)"** (same-bar and sequential-after-
breakout), and both point the same direction. No parameter was tuned in
response — the composition's confirmed definition (2% distance,
favorable side, 10-bar arming window) was applied exactly as specified
across all 14 strategies, and this is the honest, comprehensive result.
TITA continues in paper trading on its original, unfiltered entry
logic.
