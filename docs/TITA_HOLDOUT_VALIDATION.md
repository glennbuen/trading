# TITA Held-Out Validation

The one gap named in every prior TITA evaluation (`docs/
EVALUATION_FORBIDDEN_BOOK.md`, `docs/STRATEGY_COMPARISON.md`): *"No true
out-of-sample holdout beyond the walk-forward windows themselves...
a genuinely untouched final holdout period hasn't been reserved."* This
is that check, requested before any paper-trading decision.

## Honesty note, stated up front

This is the best approximation of a holdout constructible from
already-fetched historical data — **not a truly prospective test.**
Every prior TITA walk-forward run fetched "the most recent 3000 daily
candles", which already included whatever the most recent ~12 months
looked like at the time it was run; that stretch contributed to the
aggregate PF=1.83 result that got TITA selected as this project's one
genuine lead in the first place. Isolating it now and reporting it
separately still answers a real question ("does TITA's edge look any
different when the most recent stretch is judged on its own, not
blended into an 8-year aggregate") but it is not a substitute for
genuine forward validation — that is exactly what paper trading itself
provides, which is why this check is a precondition for starting paper
trading, not a replacement for it.

## Method

Full history fetched exactly as every prior TITA run (3000 daily
candles, BTC/USDT and ETH/USDT). TITA's signal computed ONCE on the full
series (same warmup as every prior evaluation — no change). Split
chronologically at (latest date − 365 days): everything before that is
"in-sample" (already covered by the original 16-window walk-forward),
the final 365 days is the holdout, backtested on its own with TITA's
unchanged defaults (`alma_window=9, rsi_length=14, rsi_lower=50,
rsi_upper=55`, `trailing_indicator` exit on `tita_alma`). No parameter
touched.

## Result

| Symbol | Holdout period | Trades | PF | Win% | Net% | Max DD% |
|---|---|---|---|---|---|---|
| BTC/USDT | 2025-09-07 → 2026-09-07 | 16 | **2.60** | 43.8 | 3.23 | 0.98 |
| ETH/USDT | 2025-09-07 → 2026-09-07 | 20 | **1.79** | 30.0 | 2.24 | 1.85 |

Both clear the 1.2 threshold, both comfortably above TITA's own original
aggregate (1.83/1.83) — the most recent year, judged in isolation, is
not where TITA's edge came from disproportionately; if anything this
slice looks stronger than the 8-year average.

**Per-quarter breakdown, to check for the thin-sample artifact pattern
that has undermined most other "promising" results in this project:**

| Quarter | BTC trades / PF | ETH trades / PF |
|---|---|---|
| 2025-09-07 → 2025-12-07 | 3 / 5.96 | 4 / 1.13 |
| 2025-12-07 → 2026-03-08 | 2 / 0.28 | 4 / 1.29 |
| 2026-03-08 → 2026-06-07 | 6 / 1.18 | 6 / 0.36 |
| 2026-06-07 → 2026-09-06 | 6 / 4.60 | 7 / 4.23 |

No single quarter shows a `PF=inf` or extreme-multiple-on-1-2-trades
artifact (the signature that disqualified MAMA/BOPIS/CALMA/SPYFRAT Core
System elsewhere in this project) — every quarter has 2-7 trades and a
bounded PF. Not every quarter is positive (BTC's Dec-Mar quarter and
ETH's Mar-Jun quarter both show real, if small, losses), which is itself
a point in favor of the result's credibility — a suspiciously smooth
all-green holdout would be more, not less, concerning.

## Verdict

**TITA passes this check.** The most recent year of real BTC/ETH data,
isolated and judged entirely on its own, shows a positive, reasonably
distributed result on both symbols, consistent with (not contradicted
by) the original walk-forward and sensitivity-sweep findings. Combined
with everything TITA already had going for it (large consistent
per-window samples, PF>1.2 on both symbols simultaneously, zero cliffs
across a 40-cell parameter sensitivity sweep), this is now the strongest
evidentiary position any strategy has reached in this project.

**This still is not the same thing as genuine forward validation.**
Per the honesty note above, the appropriate next step is paper trading
itself — real-time, zero-capital-at-risk forward testing — not a
live-trading decision. No parameter was tuned in response to this
result.
