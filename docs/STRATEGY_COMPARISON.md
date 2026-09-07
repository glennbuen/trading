# Strategy Comparison (architecture spec §24)

All four spec strategies (A: Breakout, B: Breakout+Retest, C: Trend
Pullback, D: Liquidity Sweep Reversal) evaluated with **identical**
methodology: same symbols (BTC/USDT, ETH/USDT), same timeframes (1h, 1d),
same walk-forward windows (45d/180d), same untouched risk/cost defaults,
same real OKX history. No parameter was tuned on any strategy in
response to its own results. Full individual reports:
`docs/EVALUATION_BREAKOUT_RETEST.md`, `EVALUATION_BREAKOUT.md`,
`EVALUATION_TREND_PULLBACK.md`, `EVALUATION_LIQUIDITY_SWEEP_REVERSAL.md`.

## Headline numbers

| Strategy | BTC 1h PF | ETH 1h PF | BTC 1d PF | ETH 1d PF | Avg PF | Total trades |
|---|---|---|---|---|---|---|
| B — Breakout+Retest | 0.68 | 0.88 | 1.01 | 0.73 | **0.825** | 278 |
| A — Breakout | 0.56 | 0.51 | **1.22** | 0.61 | 0.725 | 196 |
| C — Trend Pullback | 0.35 | 0.73 | 0.58 | **1.22** | 0.720 | 123 |
| D — Liquidity Sweep Reversal | 0.44 | 0.50 | 0.62 | **1.21** | 0.693 | 447 |

## Answering spec §24's questions directly

**Which has the best expectancy?** Breakout+Retest — highest average PF (0.825) across its 4 configs, and the only strategy where every single config sits above 0.68 (no config below 0.5, unlike the other three).

**Which has the lowest drawdown?** Breakout+Retest again — chained max drawdown 2.3-9.9% across its 4 configs. Liquidity Sweep Reversal is the clear worst (22.2-25.3% on 1h) — a direct consequence of its much higher trade frequency (447 total trades vs. 123-278 for the others) without a cost-aware entry filter.

**Which is most consistent?** Breakout+Retest — its 4 PF values span only 0.68-1.01 (a 0.33 range), the tightest spread of any strategy. The other three each swing roughly 3x between their best and worst config (Breakout: 0.51-1.22; Trend Pullback: 0.35-1.22; Liquidity Sweep: 0.44-1.21) — each has exactly one config that "wins" and three that clearly don't, which is a materially less stable pattern than one strategy performing evenly mediocre everywhere.

**Which works across multiple regimes?** None conclusively — but Breakout+Retest's 1d data spans the full available 2018-2026 range (bear, crash, bull, bear, recovery) with its most consistent result (PF 1.01, the closest to breakeven of anything tested on daily data), while the other three's regime coverage is thinner given far fewer 1d trades (14-67 vs. Breakout+Retest's own 22).

**Which survives out-of-sample (walk-forward window) testing best?** Average fraction of profitable windows across all 4 configs: Breakout+Retest ~35%, Trend Pullback ~28%, Liquidity Sweep Reversal ~24%, Breakout ~21%. Breakout+Retest again leads, though "leads at ~35%" is itself a statement that no strategy is winning a majority of its walk-forward windows.

**The "exception" pattern, named explicitly**: every strategy except Breakout+Retest has exactly one config that crosses PF 1.2 — and it's a *different* symbol/timeframe combination each time (Breakout: BTC/USDT 1d; Trend Pullback: ETH/USDT 1d; Liquidity Sweep Reversal: ETH/USDT 1d, the most credible of the three on sample-size grounds but still unconfirmed on BTC). No exception has ever repeated on the same symbol across strategies, and none has held on both BTC and ETH simultaneously. That inconsistency — which config "wins" scatters unpredictably rather than clustering — is itself evidence of noise around a real non-edge in each case, not a hidden signal being obscured by parameters.

## Verdict — not "which is best," but the honest §24 instruction

Spec §24 explicitly warns: *"Do not simply select the strategy with the highest historical return."* None of these four has been validated by this project's own standard (PF > 1.2, held consistently, across symbols, out-of-sample) — Breakout+Retest is the most defensible of the four **relative to the others**, on every dimension tested (expectancy, drawdown, consistency, OOS survival), but "most defensible among four unvalidated strategies" is not the same statement as "has an edge." **None of the four should proceed to paper trading as-is.** If one of these is revisited, Breakout+Retest is the one with a real methodological head start (Phase 6's parameter-sensitivity sweep already closed for it; not yet done for the other three) and the most robust starting point — not because it works, but because it's the least fragile foundation to iterate from honestly.
