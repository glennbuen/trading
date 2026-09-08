# EMA(10) Pullback Filter Retest — every strategy, new exit rules, plus one more gate

User asked to retest every strategy again, this time with an additional
entry condition ANDed onto each strategy's own entry signal: price must
be "near or within striking distance of EMA(10)". Confirmed with the
user before running (getting this wrong would mean redoing a large
sweep twice): **% distance from close to EMA(10)** (not ATR-based), and
price required **on the favorable side** — a pullback into value, not
mere proximity in either direction. For a long: close at or below the
EMA(10) but within 2% of it; the mirror for a short
(`engines/entry_filters.py`, new — built as a generic, reusable filter,
not scoped to this one retest).

Same scope, same exit system, same both-variants comparison as the
prior retest (`docs/EVALUATION_EXIT_RULES_RETEST.md`): 14 strategies
with a real entry signal, 1d only, BTC/USDT + ETH/USDT, `RiskLimits()`
defaults, flat +6% lock and ATR-trailing both run.

## Result: the filter makes things worse across the board, not better

| Strategy | Unfiltered trades (BTC/ETH) | +EMA(10) filter trades (BTC/ETH) | +EMA(10) filter PF (BTC/ETH, flat_lock) |
|---|---|---|---|
| Breakout+Retest (B) | 35 / 31 | **0 / 0** | — |
| Breakout (A) | 57 / 37 | **0 / 0** | — |
| Trend Pullback (C) | 14 / 30 | **0 / 0** | — |
| BOPIS | 91 / 97 | **0 / 0** | — |
| PAPA | 12 / 25 | **0 / 0** | — |
| Liquidity Sweep Reversal (D) | 128 / 118 | 57 / 31 | 0.69 / 0.35 |
| Ichimoku Cross | 45 / 47 | 4 / 6 | 2.41 / 0.01 |
| MFI Reversal | 93 / 70 | 32 / 15 | 0.07 / 0.37 |
| MAMA | 84 / 94 | 21 / 24 | 3.87 / 0.82 |
| TITA | 216 / 202 | **25 / 35** | **0.34 / 1.49** |
| 20% Support Bounce | 37 / 71 | 5 / 5 | 0.04 / 9.1 |
| SWAG | 66 / 62 | 7 / 1 | 0.81 / inf |
| 3-Step Formula | 208 / 195 | 69 / 30 | 0.74 / 0.71 |
| SPYFRAT Core System | 93 / 102 | 19 / 19 | 1.11 / 0.01 |

**Five of fourteen strategies (Breakout+Retest, Breakout, Trend
Pullback, BOPIS, PAPA) produce ZERO trades with this filter on either
symbol.** This is a structural, not incidental, result: these are all
breakout-style entries — by definition, a genuine breakout tends to
happen when price is EXTENDED away from a short moving average, not
pulled back near one. Requiring "near EMA(10), favorable side" is close
to definitionally incompatible with a breakout entry's own logic, not a
coincidence of this specific dataset.

**For the nine strategies that still produce trades, the picture is
uniformly worse.** Trade counts collapse (typically to the single
digits or low tens, down from 60-220), and PF results are dominated by
samples too thin to trust (Ichimoku BTC: PF 2.41 on 4 trades; 20%
Support Bounce ETH: PF 9.1 on 5 trades; SWAG ETH: PF=inf on a single
trade) — exactly the kind of number this project has learned, over and
over, not to read as a finding.

## TITA specifically: this filter hurts the strongest result in the project

TITA is the one strategy in this entire project with a large, credible,
sensitivity-tested, holdout-validated edge. Under this filter, BTC/USDT
collapses from PF 1.31 (216 trades, the already-reduced count from the
prior exit-rules retest) to **PF 0.34 on just 25 trades** — a decisive
reversal, not a marginal change. ETH/USDT nominally holds above 1.2
(1.49), but on only 35 trades, a fraction of the 202 that gave TITA's
original result its credibility. **This is strong evidence that
TITA's actual edge does NOT depend on entries happening near a
short-term EMA pullback** — RSI+ALMA momentum entries and "close to
EMA(10)" are different, not overlapping, conditions, and forcing the
overlap discards most of what was working.

## Overall verdict

**The EMA(10) proximity filter should not be added to any strategy in
this project, TITA included.** It doesn't reveal a hidden, higher-
quality subset of trades — it eliminates most of the exploitable signal
entirely (zero trades for breakout-style entries) or shrinks the sample
past the point where any PF number can be trusted, and in TITA's case
specifically, it actively destroys the one result this project has the
most confidence in. No parameter was tuned in response — the filter's
own confirmed definition (2% distance, favorable side) was applied
uniformly, exactly as specified, and this is the honest result of
testing it as specified. TITA continues in paper trading using its
original, unfiltered entry logic.
