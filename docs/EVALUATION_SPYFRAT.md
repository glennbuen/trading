# Strategy Evaluation — SPYFRAT deck's 4 testable pieces

Source: `investa-summit-2018-final-na-talaga.pptx`, a Philippine
retail-stock-trading deck ("SPYFRAT's Trading System" / "Trading Hacks"
section), the second source document tested this project (after *The
Forbidden Book*). Per explicit user instruction, all 4 pieces described in
the deck were built — including the two flagged up front as not being
faithful numeric transcriptions (Bebemon: the deck gives no numeric
definition at all; Ceiling/Follow-Through: the deck's rule depends on the
Philippine Stock Exchange's regulatory daily price up-limit, which crypto
majors don't have).

## Headline results

| Strategy | Timeframe | BTC trades / PF | ETH trades / PF | Verdict |
|---|---|---|---|---|
| **SPYFRAT Core System** | 1d | 48 / 3.01 | 48 / 2.81 | High aggregate PF, survives a sensitivity sweep, but **fails the per-window sample-size check** — see below |
| 20% Support Bounce | 1d | 23 / 0.58 | 40 / 1.85 | Fails on BTC, single-symbol-only pattern on ETH — not credible |
| Bebemon | 1d | 0 signals | 0 signals | Nothing to evaluate — the expected, honest result given this module's own caveat that it's not a transcription of the deck's (numberless) rule |
| Ceiling/Follow-Through | 1d | 0 signals | 0 signals | Nothing to evaluate — the expected, honest result given the caveat that crypto has no PSE-style price-ceiling mechanic |

## SPYFRAT Core System — a genuinely interesting result that does NOT reach TITA's level of credibility

Custom Bollinger(50, 0.20) breakout entry, exit on lower-band break OR
ePHR "sell on sight" (daily+weekly RSI(30) both >80 with daily leading) —
the deck's actual named system, and genuinely multi-timeframe (the only
strategy in this project besides the parabolic-risk classifier itself to
merge a weekly indicator onto daily bars).

This is only the **second** strategy in 14 tested this project to clear
PF>1.2 on both BTC/USDT and ETH/USDT simultaneously — TITA being the
first. That similarity made the same full scrutiny non-negotiable.

**What it has going for it:**

1. **Clears both symbols at once** (3.01 / 2.81) with a respectable trade
   count in aggregate (48 trades each).
2. **A full parameter-sensitivity sweep found no cliffs** — `bb_length`
   and `bb_std` each perturbed ±10%/±20%, both symbols (20 cells,
   `scripts/parameter_sensitivity_spyfrat.py`). Every cell stayed in the
   PF 2.1-4.65 range with 40-62 trades; several perturbations *improved*
   on baseline. This is the opposite of Ichimoku's `kijun_period` cliff.

**What undermines it — the per-window breakdown
(`scripts/spyfrat_window_check.py`), the same check that flagged
MAMA/BOPIS/CALMA:**

Unlike TITA (every one of 32 windows across both symbols had 5-14
trades), SPYFRAT's windows are thin — mostly 2-5 trades, several with
only 1-2. Categorizing each symbol's 16 walk-forward windows by whether
its net return came from a genuinely multi-trade sample or from a
handful of small windows showing a 100%-win-rate `PF=inf`:

- **BTC/USDT**: 4 of 16 windows show `PF=inf` on only 2 trades each
  (2019-12-14, 2021-06-06, 2022-11-28, 2023-05-27). Those 4 thin windows
  alone account for **~71% of the strategy's total net return** across
  all 16 windows. The single largest winning window (2020-06-11, PF
  24.63) is a 4-trade window whose profit factor implies one or two
  outsized winning trades dominating it, not a distributed edge either.
- **ETH/USDT**: 5 of 16 windows show `PF=inf` on only 2-3 trades each
  (2019-12-14, 2020-06-11, 2020-12-08, 2021-06-06, 2022-11-28). Those 5
  thin windows account for **~83% of the strategy's total net return**.

So on both symbols, the large majority of the apparent edge traces back
to a small number of thin, high-win-rate windows — the exact MAMA/BOPIS
signature (a few large winners in small samples), not TITA's (a large,
consistent sample with real variation across regimes).

**Reconciling the two checks:** passing the parameter-sensitivity sweep
does not rescue a thin-sample result — it only shows the *entry
definition* isn't fragile to small changes in band width. The same
handful of extreme historical moves that produced the `PF=inf` windows
would very plausibly still get caught by a slightly wider or narrower
band, so a clean sensitivity sweep and a thin, artifact-driven trade
sample are not actually in tension; they're answering different
questions. Both checks matter, and here they disagree on the two axes
this project treats as most decisive — which is itself the honest
result.

**Verdict: an interesting but not credible lead — closer to the
MAMA/BOPIS/CALMA end of this project's spectrum than to TITA's.** Both
symbols clearing PF>1.2 together is a weaker signal here than it was for
TITA, because most of it can be traced to a handful of individual trades
rather than a distributed edge. Not a rejection on the level of PAPA or
FISHBALL (there is a real, sensitivity-robust entry definition here, and
several genuinely multi-trade winning windows exist alongside the thin
ones), but nowhere near strong enough to treat as a second TITA-grade
finding. No parameter tuned in response to any of this.

## 20% Support Bounce — not credible

Support level = confirmed swing high × 0.80, entry only on the first-ever
touch with a same-bar reclaim. BTC/USDT fails outright (PF 0.58, only
3/16 windows profitable). ETH/USDT clears 1.85 — but this is the
familiar "works on one symbol, fails on the other" pattern flagged
repeatedly throughout this project (Breakout Strategy A, Trend Pullback's
one exception, Liquidity Sweep Reversal's ETH-only result) rather than a
new, more credible case. Given BTC's outright failure, this doesn't
warrant a per-window dig or a sensitivity sweep — the cross-symbol split
alone is disqualifying by this project's own established standard.

## Bebemon and Ceiling/Follow-Through — zero signals, the expected honest result

Both were flagged in their own module docstrings, before any real-data
run, as not being faithful transcriptions of the deck (Bebemon: the deck
never gives Segovia's pattern a numeric definition anywhere, only
visual/discretionary language; Ceiling/Follow-Through: the deck's rule
depends on the PSE's regulatory price-ceiling mechanic, which crypto
majors don't have). Real-data checks on 8 years of BTC/ETH daily data
produced 0 signals for both — consolidation-inside-the-tight-band almost
never coincides with breakout+volume for Bebemon's interpretation, and
BTC/ETH essentially never gain 15%+ in a single day twice in a row for
Ceiling/Follow-Through. Exactly the expected outcome given each caveat,
not a bug to route around — consistent with this project's rule against
loosening a definition after a disappointing (here, empty) result.

## Overall verdict

**None of the 4 SPYFRAT-deck pieces should proceed to paper trading.**
SPYFRAT Core System is the most interesting of the four — a real,
sensitivity-robust entry/exit definition that nonetheless owes most of
its historical profit to a handful of thin, high-win-rate windows rather
than a distributed edge, placing it well behind TITA and roughly
alongside MAMA/BOPIS/CALMA on this project's credibility spectrum. 20%
Support Bounce shows the familiar single-symbol pattern that has never
once held up under scrutiny in this project. Bebemon and
Ceiling/Follow-Through produced the honest zero-signal result their own
caveats predicted. No parameter was tuned in response to any of these
findings.
