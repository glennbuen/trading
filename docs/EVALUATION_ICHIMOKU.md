# Strategy Evaluation — Ichimoku Cross (spec §39)

A genuinely different hypothesis from this project's 4 spec strategies
(all of which compose price_action/market_structure/volume/liquidity,
already tested exhaustively — see `docs/STRATEGY_COMPARISON.md`). The
classic full-system Ichimoku signal (TK cross + price-vs-cloud +
projected-cloud-color + Chikou confirmation), tested faithfully on its
own terms rather than augmented with this project's other engines. Same
walk-forward methodology, symbols, timeframes, windows as every prior
evaluation — untouched defaults, nothing tuned. Kijun-sen used as the
structural stop (classic Ichimoku money management), a first for this
project (every prior strategy used ATR-only or ATR-floored stops).

A real bug was found and fixed while building this (see
`cryptobot/engines/ichimoku.py` / commit history): `~` (bitwise
inversion) on an object-dtype boolean Series doesn't do logical negation
— it made `tk_cross_up` fire on every bar after a crossover instead of
just once, at it. Fixed with the same `.astype(bool)` guard
`market_structure.py` already used for the same reason. Verified the fix
doesn't affect the 4 already-evaluated spec strategies (`grep` confirmed
the risky pattern was isolated to this new file).

| Config | Trades | Win% | PF | Avg R | Windows profitable | Chained max DD |
|---|---|---|---|---|---|---|
| BTC/USDT 1h | 84 | 33.3% | 0.60 | -0.237 | 1/7 | 9.93% |
| ETH/USDT 1h | 87 | 29.9% | 0.54 | -0.313 | 1/7 | 13.07% |
| BTC/USDT 1d | 26 | 34.6% | 0.84 | -0.105 | 6/16 | 4.13% |
| ETH/USDT 1d | 32 | **46.9%** | **1.49** | **+0.269** | 8/16 | 3.35% |

## Is ETH/USDT 1d's 1.49 real?

**The most substantive exception seen across all 5 strategies evaluated this session — still not validated, but worth more weight than the prior four.**

Reasons to take it more seriously than the previous exceptions (Breakout's BTC 1d 1.22, Trend Pullback's ETH 1d 1.22, Liquidity Sweep Reversal's ETH 1d 1.21):
- Highest PF (1.49) and highest win rate (46.9%) of any config in this entire project.
- Real multi-trade winning windows, not just small-sample flukes: PF 1.83 (4 trades), 3.81 (3 trades), 1.82 (2 trades), 3.72 (3 trades).
- **BTC/USDT 1d also improved** relative to its own strategy's ETH result (0.84 vs. 1.49) — a narrower BTC/ETH gap than any prior strategy showed (prior gaps: Breakout 1.22 vs 0.61, Trend Pullback 0.58 vs 1.22, Liquidity Sweep 0.62 vs 1.21). Still a real gap, still short of 1.0, but the closest any strategy has come to holding on both symbols.

Reasons it's still not validated:
- 4 of 16 "profitable" windows are still 100%-win-rate on just 1-2 trades (`PF=inf`) — the same artifact pattern as every prior exception, just not the *only* thing driving the number this time.
- **Real, substantive losing windows too**: three separate windows with PF exactly 0.0 on 2-3 trades each (2023-05-27, 2023-11-23, 2024-05-21) — genuine, multi-trade losses, not noise.
- **A real coverage gap**: zero trades fired at all through the back half of 2021 (2021-06-06 → 2021-12-03) — a period this strategy has simply nothing to say about.
- BTC/USDT 1d still sits below 1.0 (0.84) — the strategy has not actually confirmed on both major assets simultaneously, the same bar every prior exception has failed.
- No parameter sensitivity has been run on this strategy — unknown whether 1.49 is stable to small changes in Tenkan/Kijun/Senkou-B periods or a lucky landing spot, the same open question every strategy except Breakout+Retest still carries.

## Parameter sensitivity (spec §26) — run, and it found a real problem

Run via `scripts/parameter_sensitivity_ichimoku.py` on ETH/USDT 1d (the config that produced PF 1.49), perturbing each of the four defining parameters ±10%/±20% one at a time:

| Parameter (baseline) | PF range across ±20% | Verdict |
|---|---|---|
| `tenkan_period` (9) | 1.06 – 1.49 | Moderate peak at baseline, never collapses below 1.0 |
| `kijun_period` (26) | **0.65 – 1.49** | **Cliff** — see below |
| `senkou_b_period` (52) | 1.30 – 1.72 | Stable, actually *improves* off-default |
| `target_r_multiple` (2.0) | 1.19 – 1.49 | Smooth, no cliff |

**`kijun_period` fails spec §26's own explicit test**: *"If changing a parameter from 1.5 to 1.53 dramatically changes results, flag it as potentially overfit."* Moving Kijun from 26 to 29 bars (+10%, a completely ordinary parameter choice) collapses PF from 1.49 to **0.65** — well below breakeven. Three of the four parameters look reasonably robust in isolation, but Kijun-sen isn't a minor knob here: it also serves as this strategy's stop-loss reference, so this cliff sits at the center of the strategy's actual mechanics, not a peripheral setting.

## Verdict

**Ichimoku Cross does not have a validated edge — and the parameter-sensitivity sweep specifically undermines the one number (ETH/USDT 1d, PF 1.49) that looked most promising in this entire project.** The `kijun_period` cliff is the clearest overfitting signature found in any strategy tested this session — more diagnostic than the small-sample-window artifacts flagged in every prior strategy's exception, because it shows the result is fragile to an *ordinary* parameter choice, not just thin on trade count. Combined with BTC/USDT 1d never clearing 1.0, three multi-trade PF-0.0 windows, and the 6-month H2-2021 dead zone already noted above, this result should now be read as **less credible than it looked before this test, not more** — exactly why spec §26 asks for this check before trusting any promising number. No parameter tuned in response. Do not proceed to paper trading with this strategy.
