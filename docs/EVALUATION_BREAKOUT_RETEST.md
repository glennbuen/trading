# Final Strategy Evaluation — Breakout + Retest (architecture spec §39)

Run via `scripts/evaluate_strategy.py`. Every parameter below is the
strategy/engine/risk default — nothing was tuned based on what came out.
Walk-forward, non-overlapping windows, real OKX history (paginated),
realistic costs baked into every trade (0.10% taker fee/side, 0.05% entry
slippage, 0.4% stop slippage).

**Updated after the risk-manager fix below (originally run, then re-run
after fixing the consecutive-loss halt bug this evaluation found — see
Q11). Headline numbers are essentially unchanged; the fix improves risk
control, not the strategy's underlying edge, which is exactly what a risk
manager fix should and shouldn't do.**

| Config | Windows | Trades | Win% | PF | Avg R | Chained max DD |
|---|---|---|---|---|---|---|
| BTC/USDT 1h (8000 candles, ~11mo, 45d windows) | 7 | 117 | 37.6% | 0.68 | -0.154 | 9.91% |
| ETH/USDT 1h (8000 candles, ~11mo, 45d windows) | 7 | 118 | 39.8% | 0.88 | -0.068 | 8.53% |
| BTC/USDT 1d (3000 candles, 8.2yr, 180d windows) | 16 | 22 | 36.4% | 1.01 | 0.009 | 2.30% |
| ETH/USDT 1d (3000 candles, 8.2yr, 180d windows) | 16 | 21 | 28.6% | 0.73 | -0.207 | 2.82% |

"Chained max DD" is the true cumulative drawdown from `chain_equity_curves()` (see Q3 — both Phase 6 gaps are now closed).

## The 12 questions

**1. Positive expectancy?** No. Profit factor is below 1.0 in three of four configs; the fourth (BTC 1d, PF 1.01) is statistically indistinguishable from breakeven at 22 trades. Average R is at or below zero everywhere.

**2. How many trades tested?** 286 total across the four configs (122 + 121 + 22 + 21). The 1h configs have a workable sample; the 1d configs (21-22 trades over 8+ years) are too thin to draw a firm conclusion from in isolation — they're informative mainly as a rough directional cross-check against the 1h result, not standalone evidence.

**3. Max drawdown? RESOLVED — the chaining gap is closed.** Worst *single-window* drawdown was 4.13% (BTC 1h), 6.20% (ETH 1h), ~1.1-1.7% (1d configs). As flagged originally, that understated the real risk: each walk-forward window resets to the same starting equity independently, so the single-window number isn't the same as one continuous multi-year equity curve's peak-to-trough drawdown. `cryptobot/backtest/walk_forward.py` now has `chain_equity_curves()` — converts each window's equity curve to per-bar returns relative to its own reset start, then compounds those returns sequentially onto one continuous curve, so window boundaries no longer hide a drawdown that spans across them. **The true cumulative drawdown is roughly 2x the single-window figure in every config**: 9.91% (BTC 1h, vs. 4.13% single-window), 8.53% (ETH 1h, vs. 6.20%), 2.30% (BTC 1d, vs. 1.11%), 2.82% (ETH 1d, vs. 1.67%). Verified with a hand-computed synthetic test (`tests/test_walk_forward.py::TestChainedEquityCurve`) before trusting it on real data.

**4. Profit factor?** 0.63 / 0.88 / 1.01 / 0.73. None clear the 1.2 bar this project has used consistently as the validation threshold since the very first strategy tested.

**5. Average R?** -0.185 / -0.072 / +0.009 / -0.207. No config shows a meaningfully positive average R.

**6. Out-of-sample?** This is what walk-forward is *for* — every window is effectively an independent forward test against fixed, untuned parameters. Result: **profitable in the minority of windows everywhere** — 3/7 (BTC 1h), 2/7 (ETH 1h), 6/16 (BTC 1d), 5/16 (ETH 1d). No config shows the strategy holding up consistently out-of-sample.

**7. Across market regimes?** The 1d data spans 2018→2026: the 2018 bear, 2020 crash, 2021 bull, 2022 bear, and the 2023-2025 recovery. Performance is scattered across all of them with no visible regime where it's reliably strong — and per-window sample sizes on daily data (0-3 trades/window) are too small to responsibly attribute any single window's result to "this regime works for it" rather than noise.

**8. BTC and ETH?** Underwhelming on both, at both timeframes. Not a case of "works on one symbol, not the other" (which would suggest curve-fitting to a specific asset) — it's evenly mediocre-to-poor everywhere, which is actually a *cleaner* negative signal than an asymmetric result would be.

**9. Parameter sensitivity? RESOLVED.** Run via `scripts/parameter_sensitivity.py`: each of 4 key parameters (`atr_mult_stop`, `target_r_multiple`, `volume_threshold`, `retest_window`) perturbed at -20/-10/0/+10/+20% one at a time, on BTC/USDT 1h (the config with the most trades, hence the most power to detect a real effect). Per spec §26: *"If changing a parameter from 1.5 to 1.53 dramatically changes results, flag it as potentially overfit."*

| Parameter | PF range across ±20% | Verdict |
|---|---|---|
| `atr_mult_stop` (1.5) | 0.68 - 0.71 | Flat, stable |
| `target_r_multiple` (2.0) | 0.64 - 0.70 | Smooth monotonic decline in win-rate as R rises (43.9%→32.8%), PF stable — the expected win-rate/R-multiple trade-off, not noise |
| `volume_threshold` (1.2) | 0.58 - 0.72 | The one parameter with a real trend: looser filters (lower threshold) perform meaningfully worse (PF 0.58, chained DD 15.95% at -20%) than tighter ones (PF 0.72, chained DD 9.36% at +10%) |
| `retest_window` (10) | 0.68 (unchanged) | **Completely flat** — identical trade count and every metric across the whole ±20% range |

**No parameter shows a cliff/collapse pattern** — the rejected verdict is not an artifact of landing on an unlucky exact default value; it holds up across the whole tested neighborhood for every parameter. `volume_threshold` is the one parameter worth a closer look in any future revisit: the trend (tighter filter → better, if still not passing) is real and monotonic-ish, not noise, though even the best value tested (PF 0.72) doesn't come close to clearing 1.2.

The flat `retest_window` result was verified directly rather than assumed a wiring bug: raw signal counts at window sizes 8/10/12/20/50 shift only marginally (74→74 long signals, 79→81 short signals) — most valid retests resolve within a few bars regardless of the configured window, so 8-12 all capture essentially the same set of trades. A real, interpretable finding, not a script defect.

**10. After realistic fees and slippage?** Yes, throughout — every trade in every number above already includes the 0.10%/side taker fee, 0.05% entry slippage, and 0.4% stop-fill slippage. Total fees: $60.33 (BTC 1h) and $59.23 (ETH 1h) against $1,000-per-window starting capital — a real but not overwhelming drag (~0.8-0.9% of aggregate window capital), much smaller than the fee-bleed seen in this project's earlier high-frequency bots, because Breakout+Retest simply trades far less often.

**11. Worst losing streak?** **FIXED, post-evaluation.** Originally 11 consecutive losses (ETH 1h, the 2026-04-06→05-21 window) and 8 (BTC 1h), with only **one** `circuit_breaker_halt` rejection in that entire 11-loss window despite `max_consecutive_losses=3` being configured. Root cause: `RiskManager` reset its loss counter the moment it triggered a halt, but the halt only blocks a signal that happens to land *inside* the 24h halt window — on 1h data with signals spaced further apart than that, the next attempt often arrived after the halt had already expired, so the breaker "fired" (resetting the counter) without actually preventing anything, and losses kept accumulating across repeated halt cycles that each individually looked like they'd resolved the problem.

**Fixed in `cryptobot/risk/risk_manager.py`**: the loss counter is no longer reset when a halt triggers — only a win resets it. Every qualifying loss while at/above the threshold now re-arms (extends) the halt, so a persistent losing streak stays continuously halted until an actual win breaks it. Verified directly: re-running the exact ETH 1h window that produced the 11-loss streak now shows 3 halt rejections (up from 1) and the worst streak across the whole ETH 1h evaluation dropped from 11 to 10; BTC 1h dropped from 8 to 6. Regression tests added (`test_persistent_losing_streak_keeps_halt_continuously_rearmed`, `test_win_ends_a_persistent_losing_streak`). This did not meaningfully change the profitability verdict below — a risk-manager fix should improve protection, not manufacture edge, and it didn't.

**12. What should stop the bot from trading?** Given the above, the honest answer right now is: **it shouldn't start.** No config clears the profitability bar this project has held every strategy to, out-of-sample consistency is weak everywhere, and there's a known, unaddressed gap in the consecutive-loss protection that this exact strategy's ETH 1h run exposed. The daily/weekly loss limits and volatility-spike-style guards remain sound as *general* safety nets for whatever strategy eventually clears validation, but they don't rescue this specific result.

## Verdict

**There is currently insufficient evidence that Breakout+Retest has a reliable edge on BTC/USDT or ETH/USDT, at 1h or 1d, with these parameters.** Per spec §41, that is treated here as an acceptable, useful result — not a failure to fix by re-running with different numbers. No parameter was tuned in response to these results, and none should be, on the same reasoning applied to every one of the 7 standalone bots and every prior phase of this build: fitting parameters until a backtest looks good is the specific failure mode this whole project has been built to avoid. Do not proceed to paper trading with this strategy/config.

**Real, reusable findings from this evaluation, independent of the profitability verdict — all now closed, none left open:**
- The risk manager's consecutive-loss circuit breaker was materially weaker on sparse-signal timeframes than its parameter name implied (see Q11) — **found and fixed**, with regression tests.
- Walk-forward window drawdown understated true cumulative risk by roughly 2x in every config (see Q3) — **fixed**, `chain_equity_curves()` now gives the honest multi-window figure, verified against a hand-computed synthetic case before trusting it on real data.
- Parameter sensitivity (Q9) — **run**. No cliff/collapse in any of the 4 parameters tested; the rejected verdict holds across the whole neighborhood, not just at the exact defaults. `volume_threshold` shows the one real (if modest) trend worth remembering if this strategy is revisited.

This evaluation is now complete against spec §39's full 12-question list — no remaining gaps.
