# Day-Trading Retest — 1h+15m Trend (Both Agree), 5m Entry

User asked to redo all 14 strategies with a real entry signal as day-
trading versions: 1h and 15m for trend, 5m for entry. Confirmed scope
(all 14, not just TITA) and trend logic (both 1h and 15m must
independently agree on direction, not "1h sets direction only") before
building — see `daytrading/README.md` for the new package's structure.

Each strategy's own distinctive entry-trigger logic (`compute_*`,
unchanged) is recomputed on 5m OHLCV and gated by
`daytrading/engines/trend_filter.py` — `market_structure.trend_state()`
computed independently on 1h and 15m, merged onto the 5m timeframe via
the already-tested multi-timeframe merge engine, requiring both to show
"up" (or both "down") before an entry is allowed. Exit: plain ATR(1.5x)
stop + fixed 2R target — this project's original baseline default —
rather than either exit_rules_spec.md's system or each strategy's own
bespoke exit, since this retest is specifically about the entry
timeframe redesign, not a second exit experiment on top of it.

## A real methodological bug caught and fixed before trusting any result

The first run produced a uniformly catastrophic result across all 14
strategies (PF 0.07-0.24) — suspicious precisely because of its
uniformity across entry logics as different as breakouts, oscillator
crosses, and moving-average confluence. A diagnostic run of TITA with
NO trend filter at all showed the same catastrophic PF (0.11) as the
filtered version (0.09) — ruling out the trend filter as the cause.

The actual cause: `BacktestCosts`' project-wide default
(`stop_slippage_pct=0.4%`) was calibrated for daily-swing trading, where
a typical ATR-based stop sits several percent from entry. On 5m BTC/ETH
bars, a 1.5×ATR stop is typically **under 0.2% of price** — meaning the
0.4% slippage assumption ALONE exceeded the entire 1R risk distance,
mechanically forcing every stop-loss exit to realize more than 2R in
slippage before the trade's own P&L even mattered, regardless of the
entry signal's real quality. Corrected to a slippage assumption
realistic for BTC/USDT and ETH/USDT spot execution on OKX (deep, tight-
spread markets): 0.05% for both entry and stop fills — matching this
project's existing `entry_slippage_pct` default rather than the daily-
calibrated `stop_slippage_pct`. This materially changed individual
numbers (TITA/BTC: PF 0.09 → 0.16) but, as the full corrected run below
shows, did not change the overall verdict.

## Result (corrected cost model)

| Strategy | BTC trades / PF / win% | ETH trades / PF / win% |
|---|---|---|
| Breakout+Retest (B) | 51 / 0.12 / 13.7% | 56 / 0.17 / 19.6% |
| Breakout (A) | 31 / 0.14 / 22.6% | 38 / 0.22 / 26.3% |
| Trend Pullback (C) | 31 / 0.12 / 12.9% | 32 / 0.20 / 18.8% |
| Liquidity Sweep Reversal (D) | 85 / 0.28 / 21.2% | 81 / 0.20 / 25.9% |
| Ichimoku Cross | 61 / 0.18 / 18.0% | 64 / 0.26 / 23.4% |
| MFI Reversal | 99 / 0.31 / 29.3% | 99 / 0.36 / 29.3% |
| MAMA | 59 / 0.21 / 22.0% | 59 / 0.37 / 28.8% |
| BOPIS | 67 / 0.14 / 19.4% | 81 / 0.21 / 21.0% |
| PAPA | **0 trades** | **0 trades** |
| TITA | 121 / 0.18 / 23.1% | 116 / 0.30 / 19.8% |
| 20% Support Bounce | **0 trades** | **0 trades** |
| SWAG | 50 / 0.25 / 28.0% | 51 / 0.21 / 21.6% |
| 3-Step Formula | 143 / 0.18 / 19.6% | 143 / 0.39 / 27.3% |
| SPYFRAT Core System | 81 / 0.28 / 29.6% | 91 / 0.26 / 24.2% |

**Every strategy fails decisively — PF ranges 0.12-0.39, nowhere close
to breakeven.** Win rates are uniformly 13-30%, and every single config
sits BELOW the ~33% win rate a fixed-2R-target system needs just to
break even. This is not a thin-sample or artifact pattern requiring
further scrutiny (no per-window inspection is needed when nothing comes
remotely close to a credible PF) — it's a clean, comprehensive,
decisive rejection across every strategy, both symbols, real trade
counts (31-143 per config where any trades occur at all).

PAPA and 20% Support Bounce produce literally zero trades on either
symbol — their already-restrictive entry conditions (PAPA's MACD-zero-
cross + envelope breakout confluence; 20% Support Bounce's first-touch-
only swing-level retest) combined with requiring 1h AND 15m trend
agreement simultaneously never aligns even once across ~174 days of 5m
data on either symbol.

## Why, offered as a hypothesis not a certainty

`market_structure.trend_state()` confirms a swing only `right` bars
(default 3) after it forms — on daily/weekly bars (this project's usual
context) that's a modest few-day lag; on 1h/15m bars, a 3-bar
confirmation delay is still a real number of HOURS during which price
has already moved, and by the time the 5m entry timeframe sees a
"confirmed" 1h+15m uptrend, a meaningful fraction of that move may
already be behind it — a structural lag mismatch between a trend-
confirmation mechanism built for slower timeframes and the compressed
time scale of intraday trading. Win rates uniformly and substantially
below the fair-coin-flip baseline (33% for a 2R target) are also
consistent with entries systematically arriving late in already-
extended moves, not merely "no edge" (which would tend to land nearer
33%, not consistently well under it). This is offered as a plausible
explanation for the pattern, not a basis for adjusting the filter —
no parameter was tuned in response to this result.

## Overall verdict

**None of the 14 strategies work as redesigned day-trading systems
under this specific composition (1h+15m-both-agree trend filter, 5m
entry via each strategy's unchanged original signal, ATR/2R exit).**
This holds after correcting a real cost-model bug that would otherwise
have overstated the failure — the corrected numbers are still uniformly
decisive rejections, not close calls. No strategy in the `daytrading/`
package is ready for paper trading. TITA's swing/position version
remains this project's only validated strategy, continuing in paper
trading on its own original daily timeframe, unaffected by this result.
