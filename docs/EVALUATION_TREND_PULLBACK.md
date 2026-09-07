# Strategy Evaluation — Trend Pullback (Strategy C, spec §39)

Third of the four spec strategies. Same walk-forward methodology,
symbols, timeframes, and windows as the previous two evaluations —
nothing tuned, all defaults.

| Config | Trades | Win% | PF | Avg R | Windows profitable | Chained max DD |
|---|---|---|---|---|---|---|
| BTC/USDT 1h | 53 | 22.6% | 0.35 | -0.374 | 1/7 | 10.01% |
| ETH/USDT 1h | 38 | 36.8% | 0.73 | -0.161 | 3/7 | 5.51% |
| BTC/USDT 1d | 14 | 28.6% | 0.58 | -0.334 | 3/16 | 3.98% |
| ETH/USDT 1d | 18 | 38.9% | **1.22** | +0.137 | 6/16 | 2.54% |

## Is ETH/USDT 1d's 1.22 real?

**No — same conclusion as the Breakout strategy's BTC/USDT 1d exception, if anything on weaker evidence.** Per-window breakdown: **4 of the 6 "profitable" windows are 100%-win-rate on just 1-2 trades each** (`PF=inf`) — small-sample artifacts, not edge. 18 total trades over 8.2 years is too thin a sample to trust in isolation. And the same strategy/parameters on BTC/USDT 1d — the other major asset, same timeframe — scored a poor 0.58.

**A pattern worth naming explicitly across this project's now-3 evaluated strategies**: each time a 1d config has crossed PF 1.2, it's been a *different* symbol each time (Breakout Strategy A: BTC/USDT 1d; here: ETH/USDT 1d), on a thin sample, while the other symbol at the same timeframe scored poorly. That flip-flopping — which symbol "wins" isn't consistent strategy to strategy — is itself evidence this is noise scattering around a real non-edge, not signal. A genuine edge would be expected to show up on the *same* symbol repeatedly, or at least on both, not alternate unpredictably depending on which strategy happens to be tested.

## Verdict

**Trend Pullback does not have a validated edge.** Worse than both previously-evaluated strategies on 1h (PF 0.35/0.73 vs Breakout+Retest's 0.68/0.88 and Breakout's 0.56/0.51 — actually the worst BTC 1h result of the three strategies tested so far). The one number crossing 1.2 fails the same sample-size and cross-symbol bars every prior "promising" number in this project has failed. No parameter tuned in response. Do not proceed to paper trading with this strategy.

## One strategy-design finding worth recording

Testing this strategy's synthetic fixtures surfaced a real interaction worth understanding (not a bug, documented in `cryptobot/strategies/trend_pullback.py`): if a strategy's own "continuation" candle happens to independently qualify as a fresh strong-candle impulse, it starts a *new* episode rather than confirming the old one — because `episode_id = impulse_event.cumsum()` increments on that same bar. This is defensible behavior (a big new impulse candle arguably is a fresh setup), the same as how Breakout+Retest's `breakout_event` can also legitimately retrigger on an independent subsequent breakout — but it's a real, non-obvious consequence of the episode-scan technique used across all of this project's multi-bar strategies, worth remembering if either strategy's signal counts ever look lower than expected on real data.
