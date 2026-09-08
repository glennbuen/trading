# Exit Rules Retest — exit_rules_spec.md vs. Every Strategy's Original Exit

User provided `exit_rules_spec.md` ("Exit Rules Spec — Daily Timeframe
Swing/Position Trades") and asked to retest every strategy against it.
This replaces each strategy's ORIGINAL exit mechanism (trailing-
indicator, structure-based, fixed-ATR, or a bespoke signal-exit)
entirely with the new system — only entry logic is reused, unchanged,
from each strategy's existing `compute_*` function.

## What the new exit system is

A 5-rule position-management state machine (`cryptobot/backtest/
exit_rules.py` + `exit_rules_engine.py`), built and unit/integration
tested (34 tests) before this retest: a ratcheted hard % stop (initial
5%, breakeven at +4%, locked at +12%), a time stop (tighten at day 5,
exit allowed at day 6 if the trade hasn't moved), a one-time +20%
partial profit-take (25%), and a two-stage EMA(8)/EMA(4) de-risk (sell
50% on an EMA(8) close-break, exit the rest on a failed reclaim or an
EMA(4)/EMA(8) cross against the position). Two confirmed variants tested
throughout, per explicit user confirmation before building the spec's
own flagged "ADDITION": the original flat +6% lock above +12% profit,
and an ATR-trailing alternative (`stop = highest_price_since_entry −
2.5×ATR(14)`, only ever moves up).

## Scope — 1d only, 14 of the 20 strategies tested this project

The spec is explicitly titled "Daily Timeframe Swing/Position Trades"
and built entirely around daily-close mechanics — this doesn't
translate to a sub-daily or weekly-native strategy's own timeframe.
Retested on each strategy's 1d configuration only, BTC/USDT + ETH/USDT,
180-day walk-forward windows, `RiskLimits()` defaults (matching every
prior 1d evaluation in this project exactly, for a fair comparison).

**Excluded**: Bebemon, Ceiling/Follow-Through (zero real-data entry
signals — a different exit system can't create trades from no entries);
FISHBALL (30m-native), Day Trading ALMA (15m-native), 4-Hour Range Scalp
(5m-native), CALMA (1w-native) — a 5-8 DAY time stop and daily-close EMA
rules don't apply to a strategy's own non-daily timeframe.

## Headline results — flat +6% lock variant (see below for why this variant, not ATR-trailing, is used as the primary comparison)

| Strategy | Original 1d PF (BTC/ETH) | New 1d PF (BTC/ETH) | Trades (BTC/ETH) | Verdict |
|---|---|---|---|---|
| TITA | 1.83 / 1.83 | 1.31 / 1.99 | 216 / 202 | **Still clears both — genuinely credible, see below** |
| SPYFRAT Core System | 3.01 / 2.81 | 1.54 / 1.51 | 93 / 102 | **Lower PF, but MORE credible — thin-sample artifact greatly reduced** |
| Breakout (A) | 1.22 / 0.61 | 1.50 / 1.64 | 57 / 37 | Now "clears both" — but per-window inspection shows the same thin-sample artifact pattern that disqualified MAMA/BOPIS/CALMA |
| Ichimoku Cross | 0.84 / 1.49 | 1.50 / 1.45 | 45 / 47 | Same thin-sample artifact — several 0-1-trade windows, `PF=inf` on tiny samples |
| MAMA | 2.25 / 2.68 | 1.69 / 2.05 | 84 / 94 | Still thin-sample-artifact-driven (windows: 0, 2-11 trades, PF up to 78.83 on 7 trades) |
| BOPIS | 1.75 / 2.17 | 1.04 / 1.80 | 91 / 97 | BTC now fails (<1.2) — the "both symbols" clear from the original exit evaporates |
| Liquidity Sweep Reversal (D) | 0.62 / 1.21 | 1.05 / 1.22 | 128 / 118 | Marginal on both — neither decisively clears |
| Breakout+Retest (B) | 1.01 / 0.73 | 1.13 / 0.87 | 35 / 31 | Roughly unchanged, still fails |
| Trend Pullback (C) | 0.58 / 1.22 | 0.21 / 2.15 | 14 / 30 | BTC gets worse; still single-symbol only |
| MFI Reversal | 0.49 / 1.08 | 0.33 / 0.59 | 93 / 70 | Worse on both — clean rejection persists |
| PAPA | 0.65 / 0.14 | 0.69 / 0.45 | 12 / 25 | Still fails both |
| 20% Support Bounce | 0.58 / 1.85 | 0.18 / 0.75 | 37 / 71 | ETH's original exception evaporates — now fails both |
| SWAG | 1.26 / 0.89 | 1.14 / 1.04 | 66 / 62 | BTC's original exception evaporates — now fails both |
| 3-Step Formula | ~0 (0-8 trades) | 1.10 / 0.79 | 208 / 195 | Now a real sample (the new system has no RR filter) — still fails both, a MORE decisive rejection than before |

## The central finding: flat +6% lock beats the ATR-trailing addition, decisively

The user asked to build both the original flat-lock rule and the
spec's own flagged "ADDITION" (ATR-trailing above +12%) and compare
them. Across all 28 strategy/symbol combinations tested: **the flat
lock produces a higher PF in 21 of 28 (75%)**, the ATR-trailing variant
wins in 4 (Ichimoku Cross on both symbols, PAPA on both symbols — none
of which are credible results anyway, see above), and 3 are ties. The
average-R-multiple pattern is even more consistent: flat_lock's avgR is
higher than atr_trailing's in nearly every single row of the raw output
(`scripts/retest_all_with_exit_rules.py`'s full output).

**A plausible reason, offered as an observed pattern from this data, not
a certainty**: `2.5 × ATR(14)` on daily BTC/ETH candles is frequently a
*wider* distance from the recent high than a flat 6% lock is from entry
— so on the much more common case where a trade doesn't run
dramatically past +12% before reversing, the ATR-trailing stop gives
back more before exiting than the flat lock does. The ATR-trailing
addition's own stated rationale (protect more of an exceptional runner
that goes 30%+) is real in principle, but exceptional runners are rare
enough in this data that the wider stop's cost in the ordinary case
outweighs the benefit in the rare case, on net.

**This directly answers the question the user asked when confirming the
addition should be built and compared, not silently chosen: the
spec's original flat +6% lock is the better default for this test
suite.** The ATR-trailing variant remains available
(`enable_atr_trailing_above_lock=True`) for cases where a strategy is
specifically expected to produce large trending runners, but isn't a
uniform improvement.

## TITA: exit_rules_spec.md is a genuine (if slightly weaker) exit for this strategy

Per-window inspection (`scripts/exit_rules_per_window_check.py`) shows
TITA is the ONE strategy in this retest where the new exit system's
result is unambiguously credible on its own terms, not a thin-sample
artifact: every one of 16 windows on both symbols has 7-21 trades (never
below 7), with real variation across regimes (several genuinely negative
windows, e.g. -2.41%, -2.35%, -2.07% net — not a suspiciously smooth
curve). PF (1.31 BTC / 1.99 ETH) is lower than TITA's own bespoke
trailing-ALMA exit (1.83 / 1.83), and BTC's 1.31 is closer to the 1.2
threshold than its original result — but this is a genuinely different,
larger trade sample (216 vs 166 trades on BTC, since the new system's
partial exits and tighter percentage stop produce more, smaller slices),
and it still clears both symbols under the new system.

**Honest conclusion: TITA's own book-derived exit (RSI+ALMA trailing)
is better matched to its entry logic than this generic 5-rule system.**
That is itself a useful, non-obvious finding — a more sophisticated,
more thoroughly-specified exit system doesn't automatically outperform
a simpler one that happens to fit the entry signal's own rhythm. This
does NOT change the recommendation already in place: TITA continues in
paper trading using its own original exit (trailing ALMA + ATR floor),
not this new system — switching would be a live-system change made
without evidence it's actually an improvement for TITA specifically.

## SPYFRAT Core System: a genuine improvement in credibility, not just a different number

SPYFRAT Core System's original evaluation (`docs/EVALUATION_SPYFRAT.md`)
found that 71-83% of its net return traced to a handful of 2-3-trade
`PF=inf` windows — closer to the MAMA/BOPIS/CALMA artifact pattern than
to TITA's. Under the new exit system, per-window trade counts are
substantially larger and more evenly distributed (BTC: mostly 3-11
trades per window; ETH: mostly 4-12) — a real, structural improvement in
sample quality, even though the headline PF is lower (1.54/1.51 vs.
3.01/2.81). One outlier window (BTC, 2023-05-28: PF=139.94 on 9 trades)
still shows a large-multiple-winner skew worth noting, but this is a
materially more credible result than the original. **Not elevated to
TITA's tier — no parameter-sensitivity sweep has been run on this
config yet, and one extreme-PF window remains a real caveat — but a
genuine step up from "artifact-driven" to "worth a further look",
achieved by changing only the exit mechanism.**

## Breakout (A), Ichimoku Cross, MAMA: the same thin-sample artifact, wearing a different exit

All three newly (or still) clear PF>1.2 on both symbols under the new
exit system, but per-window inspection shows the identical pattern that
disqualified every other artifact-driven "exception" throughout this
project: multiple 0-1-trade windows, `PF=inf` or extreme multiples (up
to 78.83 on MAMA's BTC, 21.07/13.54 on Breakout A's ETH) on samples too
small to mean anything. Ichimoku Cross in particular already failed a
parameter-sensitivity cliff test under its ORIGINAL exit system
(`docs/EVALUATION_ICHIMOKU.md`) — a different exit mechanism doesn't
change the underlying fragility of its entry signal. **None of these
three should be read as newly promising** — the exit system changed,
the underlying sample-size problem didn't.

## Strategies whose prior single-symbol "exception" evaporates entirely

BOPIS (BTC), 20% Support Bounce (ETH), and SWAG (BTC) each previously
had one symbol clearing (or nearly clearing) 1.2 under their original
exit mechanism. Under the new exit system, all three of those specific
exceptions drop below 1.2 — consistent with this project's repeated
finding that a single-symbol "exception" which depends on the specific
exit mechanism used is exactly the kind of noise this project's
credibility ladder is designed to catch, not a hidden edge.

## Overall verdict

**exit_rules_spec.md does not change this project's central conclusion.**
TITA remains the standout, and this retest adds a genuinely useful data
point: TITA's own bespoke exit outperforms this more elaborate generic
system, which is itself informative about how well-matched an exit
needs to be to its entry logic. SPYFRAT Core System is meaningfully more
credible under this new exit system than under its own, though still one
step behind TITA. Every other strategy's headline PF change under the
new system is explained by the same causes this project has documented
repeatedly — thin-sample artifacts or single-symbol noise — not a
genuine improvement. The flat +6% lock beats the ATR-trailing addition
across this test suite by a clear margin (21 of 28 configs), directly
answering the comparison the user asked for. No parameter was tuned in
response to any of these results; the exit system's own defaults (or
its user-confirmed ATR-trailing toggle) were applied uniformly.
