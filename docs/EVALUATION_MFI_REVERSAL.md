# Strategy Evaluation — MFI Reversal (spec §39)

A genuinely different hypothesis from every prior strategy this session
— the classic textbook Money Flow Index oversold/overbought reversal
signal (MFI reclaims 20 from below = long, loses 80 from above = short),
tested faithfully on its own terms, ATR-based exits (same framework as
most strategies here, for direct comparability). Same walk-forward
methodology, symbols, timeframes, windows as every prior evaluation —
untouched defaults, nothing tuned.

| Config | Trades | Win% | PF | Avg R | Windows profitable | Fees | Chained max DD |
|---|---|---|---|---|---|---|---|
| BTC/USDT 1h | 144 | 27.1% | 0.39 | -0.352 | **0/7** | $70.11 | 22.64% |
| ETH/USDT 1h | 150 | 31.3% | 0.59 | -0.274 | 1/7 | $71.84 | 18.74% |
| BTC/USDT 1d | 51 | 21.6% | 0.49 | -0.421 | 3/16 | $7.72 | 11.15% |
| ETH/USDT 1d | 41 | 39.0% | 1.08 | +0.051 | 8/16 | $4.78 | 3.15% |

## The weakest strategy of the 6 tested this session

Average PF across its 4 configs: **0.6375** — the lowest of any strategy evaluated (Breakout+Retest 0.825, Breakout 0.725, Trend Pullback 0.720, Liquidity Sweep Reversal 0.693, Ichimoku Cross 1.0175 including its since-undermined exception). BTC/USDT 1h is the worst 1h result of any strategy (PF 0.39, 0 of 7 windows profitable) alongside high frequency and heavy fee drag ($70+/config on 1h) — the same fee-bleed-from-overtrading pattern already seen in Liquidity Sweep Reversal.

## Is ETH/USDT 1d's 1.08 worth a closer look?

**No — it doesn't even clear the 1.2 threshold this project has used throughout, so unlike Ichimoku's 1.49 there's no promising number here to interrogate with a parameter-sensitivity sweep.** 1.08 with a barely-positive avg R (+0.051) is close to breakeven, not evidence of edge — and it's still the only one of four configs anywhere near workable, with the other three ranging from poor to the worst-in-project.

## Verdict

**MFI Reversal does not have a validated edge, and is the weakest performer of the 6 strategies tested this session.** The classic oscillator-reversal signal, tested faithfully without embellishment, simply doesn't hold up on this data — worse than every prior strategy on both 1h configs, and its best config falls short of even the threshold that prompted a closer look at Ichimoku. No parameter tuned in response. Do not proceed to paper trading with this strategy.
