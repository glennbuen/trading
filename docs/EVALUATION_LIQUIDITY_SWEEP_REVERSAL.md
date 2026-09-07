# Strategy Evaluation — Liquidity Sweep Reversal (Strategy D, spec §39)

Fourth and last of the four spec strategies. Same walk-forward
methodology, symbols, timeframes, and windows as the previous three —
nothing tuned, all defaults.

| Config | Trades | Win% | PF | Avg R | Windows profitable | Fees | Chained max DD |
|---|---|---|---|---|---|---|---|
| BTC/USDT 1h | 163 | 30.1% | 0.44 | -0.304 | 0/7 | $80.03 | 22.18% |
| ETH/USDT 1h | 165 | 29.7% | 0.50 | -0.328 | 1/7 | $79.56 | 25.29% |
| BTC/USDT 1d | 67 | 26.9% | 0.62 | -0.302 | 5/16 | $11.05 | 10.69% |
| ETH/USDT 1d | 52 | 42.3% | **1.21** | +0.130 | 8/16 | $6.25 | 3.95% |

## By far the highest-frequency of the four strategies — and it shows

448 raw signals over ~11 months of 1h data (vs. 57-122 for the other three), because unlike Breakout+Retest/Trend Pullback's multi-bar episode-gated patterns, a sweep-and-reclaim resolves within `max_bars_to_reclaim` (3) bars by construction — a structurally faster-firing setup. The 1h configs pay for it directly: **0/7 and 1/7 profitable windows**, the worst of any config across all four strategies, and **chained drawdown of 22-25%** — more than double the worst drawdown seen in any prior strategy (Breakout+Retest's worst was 9.91%). Fees ($80/config) are also the highest of any strategy tested. This is the same fee-bleed-from-overtrading pattern this project first identified in the standalone `okx_scalper_bot.py`/`okx_bollinger_bot.py`, showing up again in the cryptobot package's highest-frequency strategy.

## Is ETH/USDT 1d's 1.21 real?

**More credible than the previous three strategies' PF>1.2 exceptions, but still short of validated.** Per-window breakdown (16 windows, 52 trades) shows only **one** small-sample artifact (a single 100%-win-on-1-trade window) — the rest have 3-5 trades each with believable win rates (0%, 25%, 33%, 50%, 60%, 66%, 75%) and a real spread of outcomes (several strong windows: PF 2.19, 3.22, 5.46, 2.77, 2.23; several weak: 0.0, 0.64, 0.0, 0.6). 8 of 16 windows profitable — a genuine near-50/50 split, not a lucky minority propped up by one or two flukes.

That said, it still doesn't clear the bar this project has held throughout:
- **Doesn't hold on BTC/USDT 1d, same timeframe, same parameters** (PF 0.62 — a real, not marginal, gap).
- 52 trades over 8.2 years is still a modest sample by any standard.
- No parameter sensitivity has been run on this strategy (same gap noted for Breakout Strategy A and Trend Pullback — only Breakout+Retest has had this closed, in the Phase 6 follow-up).

## Verdict

**Liquidity Sweep Reversal does not have a validated edge**, and is the worst-performing of the four strategies overall on 1h timeframes (0/7 and 1/7 profitable windows, severe drawdown, heaviest fee load) — a direct, real-data confirmation of the "high signal frequency without a cost-aware mechanism erodes results" finding first surfaced in the standalone-bot phase of this project. ETH/USDT 1d is the single most credible positive result seen across all 4 strategies evaluated so far, but "most credible of four rejected exceptions" is not the same as "validated" — it fails the same cross-symbol bar every prior exception has failed. No parameter tuned in response to any of these results. Do not proceed to paper trading with this strategy.
