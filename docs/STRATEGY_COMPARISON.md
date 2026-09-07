# Strategy Comparison and Rankings

Every strategy this project has built and evaluated, ranked by **evidence
credibility**, not raw historical PF — spec §24 explicitly warns
*"do not simply select the strategy with the highest historical
return,"* and this project's own findings prove why: several of the
highest raw PF numbers below (CALMA 9.32, SPYFRAT Core System 3.01,
Ichimoku 1.49) turned out to be the least trustworthy once inspected,
while the most trustworthy result (TITA, PF 1.83) is nowhere near the
highest number on the list.

**The credibility ladder used to rank, strongest evidence first:**
1. Clears PF>1.2 on BOTH BTC/USDT and ETH/USDT simultaneously.
2. Large, consistent per-window trade counts (no small-sample
   `PF=inf`/extreme-PF windows driving the aggregate).
3. Survives a parameter-sensitivity sweep (±10%/±20% on key params, no
   cliffs).

A strategy is ranked by how far up this ladder it actually got, not by
how good its headline number looks before that scrutiny is applied.

## Master ranking — all 20 strategies tested

### Tier 1 — Genuine lead (cleared every rung)

| Strategy | Source | BTC PF (trades) | ETH PF (trades) | Sensitivity sweep |
|---|---|---|---|---|
| **TITA** | Forbidden Book | 1.83 (166) | 1.83 (158) | **Zero cliffs**, 40 cells |

The only strategy in this project with a large, consistent per-window
sample on both symbols (5-14 trades every window) AND a clean
sensitivity sweep. Full report: `docs/EVALUATION_FORBIDDEN_BOOK.md`.

### Tier 2 — Passes sensitivity, but undermined by a thin per-window sample

| Strategy | Source | BTC PF (trades) | ETH PF (trades) | Sensitivity sweep |
|---|---|---|---|---|
| SPYFRAT Core System | SPYFRAT deck | 3.01 (48) | 2.81 (48) | Zero cliffs, 20 cells — but 71-83% of net return traces to a handful of 2-3-trade `PF=inf` windows |

Clears both symbols and a clean sensitivity sweep — the same two checks
TITA passed — but fails the per-window check TITA also passed. Passing
sensitivity shows the *entry definition* isn't fragile; it says nothing
about whether the trade sample is large enough to trust, and here it
isn't. Full report: `docs/EVALUATION_SPYFRAT.md`.

### Tier 3 — Promising number, specifically falsified by a sensitivity cliff

| Strategy | Source | BTC PF | ETH PF | Sensitivity sweep |
|---|---|---|---|---|
| Ichimoku Cross | Requested directly | 0.84 | 1.49 | `kijun_period` +10% collapses PF 1.49 → 0.65 |

Only tested on 1 symbol's exception (never cleared both simultaneously),
but the one strategy that got far enough to have a real cliff *found* —
a more decisive rejection than most below, which never got a sensitivity
sweep because a cheaper check already disqualified them first. Full
report: `docs/EVALUATION_ICHIMOKU.md`.

### Tier 4 — High aggregate PF, disqualified by thin-sample artifacts before a sweep was warranted

| Strategy | Source | BTC PF (trades) | ETH PF (trades) |
|---|---|---|---|
| CALMA | Forbidden Book | 6.36 (15) | 9.32 (14) |
| MAMA | Forbidden Book | 2.25 (47) | 2.68 (58) |
| BOPIS | Forbidden Book | 1.75 (61) | 2.17 (66) |

All three clear both symbols on paper, but per-window inspection shows
individual 1-4-trade windows with PF as extreme as 46.33 — a few large
winners in thin samples, not a distributed edge. None received a
sensitivity sweep; the per-window evidence already disqualified them the
same way it disqualified every non-TITA "exception" elsewhere in this
project. Full report: `docs/EVALUATION_FORBIDDEN_BOOK.md`.

### Tier 5 — Single-symbol/single-config exception only, the rest fail

| Strategy | Config that "wins" | Winning PF | Other configs |
|---|---|---|---|
| Breakout (Strategy A) | BTC/USDT 1d | 1.22 | 0.51-0.61 elsewhere |
| Trend Pullback (Strategy C) | ETH/USDT 1d | 1.22 | 0.35-0.73 elsewhere |
| Liquidity Sweep Reversal (Strategy D) | ETH/USDT 1d | 1.21 | 0.44-0.62 elsewhere |
| 20% Support Bounce | ETH/USDT 1d | 1.85 | 0.58 on BTC/USDT |
| SWAG Trading System | BTC/USDT 1d | 1.26 | 0.52-0.89 elsewhere, and BTC's own per-window detail is thin-sample-driven too |

**Named pattern**: each exception is on a *different* symbol/timeframe,
never repeats across strategies, and never holds on both BTC and ETH at
once — evidence of noise scattering around a real non-edge, not a
hidden signal. Liquidity Sweep Reversal's exception is the most credible
of this tier on sample-size grounds (52 trades) but still unconfirmed on
BTC; it's also the worst strategy on 1h of any tested (chained drawdown
22-25%, heaviest fee load). Full reports: `docs/EVALUATION_BREAKOUT.md`,
`EVALUATION_TREND_PULLBACK.md`, `EVALUATION_LIQUIDITY_SWEEP_REVERSAL.md`,
`EVALUATION_SPYFRAT.md`, `EVALUATION_SWAG.md`.

### Tier 6 — Consistently mediocre, no exception anywhere

| Strategy | Avg PF across configs | Range |
|---|---|---|
| Breakout+Retest (Strategy B) | 0.825 | 0.68-1.01 |
| MFI Reversal | 0.6375 | 0.39-1.08 |

Breakout+Retest never crosses 1.2 anywhere, but it's also the tightest,
most stable strategy tested (no config below 0.68) — the least fragile
foundation of the four original spec strategies, not because it works.
MFI Reversal is weaker on every axis, including the worst 1h result of
any strategy (0.39, 0/7 windows profitable). Full reports:
`docs/EVALUATION_BREAKOUT_RETEST.md`, `EVALUATION_MFI_REVERSAL.md`.

### Tier 7 — Fails outright on every config tested

| Strategy | BTC PF | ETH PF |
|---|---|---|
| PAPA | 0.65 | 0.14 |
| SWAG (1h) | 0.52 | 0.53 |
| 4-Hour Range Scalp | 0.43 | 0.40 |
| FISHBALL | 0.03 | 0.33 |
| Day Trading (ALMA) | 0.18 | 0.08 |

FISHBALL and Day Trading show the fee-bleed-from-overtrading signature
(30m/15m timeframes). PAPA's own stated design goal (filtering out
explosive moves) may simply not translate to crypto's baseline
volatility. **4-Hour Range Scalp is worth singling out as the cleanest,
best-sampled rejection in this entire tier** — 138/129 trades spread
evenly across 12 walk-forward windows per symbol (5-19 trades every
window, never a thin/artifact window), so this isn't "not enough data
to tell" the way several other results in this project are — it's a
confident, well-evidenced negative result. Full reports:
`docs/EVALUATION_FORBIDDEN_BOOK.md`, `EVALUATION_SWAG.md`,
`EVALUATION_FOUR_HOUR_RANGE_SCALP.md`.

### Tier 8 — Near-zero or zero real-data signal count, nothing meaningful to evaluate

| Strategy | Result |
|---|---|
| 3-Step Formula | 0-8 trades per config (BTC/ETH, 1h/1d) — a strict, faithful reading of its own RR≥2.5 rule prunes nearly all candidates; a diagnostic run with that filter removed shows the underlying setup is negative-expectancy anyway (PF 0.89/0.72) |
| Bebemon | 0 signals, both symbols — expected, given the module's own caveat that the deck gives no numeric definition |
| Ceiling/Follow-Through | 0 signals, both symbols — expected, given crypto has no PSE-style price-ceiling mechanic |

Full reports: `docs/EVALUATION_THREE_STEP_FORMULA.md`,
`EVALUATION_SPYFRAT.md`.

## Overall verdict

**20 strategies tested, exactly one — TITA — has cleared every rung of
this project's own credibility ladder.** SPYFRAT Core System is the only
other strategy to reach the second rung, and it stops there. Every other
result this project has produced, no matter how high its raw PF looked
before scrutiny, has been explained by one of: a single-symbol fluke, a
thin trade sample propped up by a few large winners, a parameter cliff,
or outright failure. **No parameter has been tuned in response to any
result in this project, ever** — every ranking above reflects the
strategy/engine defaults, run once, reported as-is. Only TITA is a
genuine lead worth a real follow-up (a true held-out confirmation
period, additional symbols); nothing here should proceed to paper
trading yet, TITA included.

---

## Appendix — the original spec §24 comparison (4 spec strategies only)

Kept for its original narrower context: the very first head-to-head
comparison this project ran, using identical methodology (same symbols,
timeframes, walk-forward windows, untouched risk/cost defaults) across
just the 4 architecture-spec strategies, before any of the later
strategies (Ichimoku onward) existed to compare against.

| Strategy | BTC 1h PF | ETH 1h PF | BTC 1d PF | ETH 1d PF | Avg PF | Total trades |
|---|---|---|---|---|---|---|
| B — Breakout+Retest | 0.68 | 0.88 | 1.01 | 0.73 | **0.825** | 278 |
| A — Breakout | 0.56 | 0.51 | **1.22** | 0.61 | 0.725 | 196 |
| C — Trend Pullback | 0.35 | 0.73 | 0.58 | **1.22** | 0.720 | 123 |
| D — Liquidity Sweep Reversal | 0.44 | 0.50 | 0.62 | **1.21** | 0.693 | 447 |

**Which has the best expectancy?** Breakout+Retest — highest average PF (0.825) across its 4 configs, and the only strategy where every single config sits above 0.68 (no config below 0.5, unlike the other three).

**Which has the lowest drawdown?** Breakout+Retest again — chained max drawdown 2.3-9.9% across its 4 configs. Liquidity Sweep Reversal is the clear worst (22.2-25.3% on 1h) — a direct consequence of its much higher trade frequency (447 total trades vs. 123-278 for the others) without a cost-aware entry filter.

**Which is most consistent?** Breakout+Retest — its 4 PF values span only 0.68-1.01 (a 0.33 range), the tightest spread of any strategy. The other three each swing roughly 3x between their best and worst config (Breakout: 0.51-1.22; Trend Pullback: 0.35-1.22; Liquidity Sweep: 0.44-1.21) — each has exactly one config that "wins" and three that clearly don't, which is a materially less stable pattern than one strategy performing evenly mediocre everywhere.

**Which works across multiple regimes?** None conclusively — but Breakout+Retest's 1d data spans the full available 2018-2026 range (bear, crash, bull, bear, recovery) with its most consistent result (PF 1.01, the closest to breakeven of anything tested on daily data), while the other three's regime coverage is thinner given far fewer 1d trades (14-67 vs. Breakout+Retest's own 22).

**Which survives out-of-sample (walk-forward window) testing best?** Average fraction of profitable windows across all 4 configs: Breakout+Retest ~35%, Trend Pullback ~28%, Liquidity Sweep Reversal ~24%, Breakout ~21%. Breakout+Retest again leads, though "leads at ~35%" is itself a statement that no strategy is winning a majority of its walk-forward windows.

**The "exception" pattern, named explicitly**: every strategy except Breakout+Retest has exactly one config that crosses PF 1.2 — and it's a *different* symbol/timeframe combination each time. No exception has ever repeated on the same symbol across strategies, and none has held on both BTC and ETH simultaneously. That inconsistency — which config "wins" scatters unpredictably rather than clustering — is itself evidence of noise around a real non-edge in each case, not a hidden signal being obscured by parameters.

Spec §24 explicitly warns: *"Do not simply select the strategy with the highest historical return."* None of these four was validated by this project's own standard — Breakout+Retest was the most defensible of the four **relative to the others**, on every dimension tested, but "most defensible among four unvalidated strategies" is not the same statement as "has an edge." This narrower verdict has since been superseded by the master ranking above, once later strategies (especially TITA) gave this project an actual positive case to compare against.
