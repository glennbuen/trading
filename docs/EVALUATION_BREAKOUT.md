# Strategy Evaluation — Breakout (Strategy A, spec §39)

Built as the direct "control" comparison to Breakout+Retest (Strategy B,
Phase 4/6): same core (structural break + volume confirmation), but
enters ON the breakout with no wait for a retest, plus an explicit
consolidation-before-breakout filter ("reject weak breakouts", spec §10)
that Breakout+Retest doesn't have. Same walk-forward methodology, same
symbols/timeframes/windows, same untouched defaults — nothing tuned.

| Config | Trades | Win% | PF | Avg R | Windows profitable | Chained max DD |
|---|---|---|---|---|---|---|
| BTC/USDT 1h | 73 | 32.9% | 0.56 | -0.216 | 0/7 | 8.19% |
| ETH/USDT 1h | 67 | 31.3% | 0.51 | -0.321 | 1/7 | 11.80% |
| BTC/USDT 1d | 31 | 41.9% | **1.22** | +0.144 | 7/16 | 2.76% |
| ETH/USDT 1d | 25 | 24.0% | 0.61 | -0.305 | 4/16 | 6.40% |

## Comparison to Breakout+Retest (same symbols/timeframes/windows)

| Config | Breakout PF | Breakout+Retest PF | Retest requirement helped? |
|---|---|---|---|
| BTC/USDT 1h | 0.56 | 0.68 | Yes — meaningfully |
| ETH/USDT 1h | 0.51 | 0.88 | Yes — meaningfully |
| BTC/USDT 1d | **1.22** | 1.01 | **No** — plain breakout did better here |
| ETH/USDT 1d | 0.61 | 0.73 | Yes — modestly |

**Answers the question this strategy was built to test**: on 3 of 4 configs, requiring a retest-and-hold before entry genuinely helped — the raw breakout is worse everywhere except one config. That's a real, useful finding independent of whether either strategy is tradeable.

## Is BTC/USDT 1d's 1.22 real?

**No — not on this evidence, despite being the first config in this entire project (7 standalone bots + 2 cryptobot strategies) to numerically clear the 1.2 bar.** Reasons for skepticism, not enthusiasm:

1. **Thin sample.** 31 trades over 8.2 years. Per-window breakdown shows 2 of the "profitable" windows are 100%-win-rate on just 1-3 trades each (`PF=inf`) — a classic small-sample artifact, not evidence of edge.
2. **Doesn't hold on ETH.** ETH/USDT 1d, same strategy, same parameters, same period: PF 0.61 — a real, poor result. A genuine edge in a trend/breakout mechanism would be expected to show up on both major assets to some degree; this divergence (great on BTC, bad on ETH) is exactly the "works on one symbol only" pattern this project has flagged as a curve-fitting/noise red flag every time it's appeared before (e.g. `okx_trend_bot.py` in the original 7 bots).
3. **Not walk-forward-consistent even within BTC.** 7/16 profitable windows is a bare plurality, not a strong majority — and several of the "unprofitable" windows are 0% win rate outright (PF 0.0), not just marginal losses.
4. **No parameter sensitivity run yet** on this strategy (unlike Breakout+Retest, where that gap was explicitly closed in Phase 6's follow-up). Unknown whether this number is stable to small parameter changes or a lucky landing spot.

## Verdict

**Breakout (Strategy A) does not have a validated edge either — same conclusion as Breakout+Retest, for the same reason (insufficient evidence, not proof of absence).** It is directionally worse than Breakout+Retest in 3 of 4 configs, confirming the retest requirement is doing real work, not just filtering trades arbitrarily. The one number that clears the historical threshold (BTC 1d, PF 1.22) is the most interesting single data point across this entire project, but fails the same cross-symbol and sample-size bars every other strategy has been held to — treated as a lead worth revisiting with a larger sample and a sensitivity sweep, not as a result. Do not proceed to paper trading with this strategy.
