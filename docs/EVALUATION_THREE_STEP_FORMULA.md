# Strategy Evaluation — "3-Step Formula" (YouTube price-action video)

Source: the user's own transcript of a YouTube trading video ("I have a
3 step formula that I've backtested 1000s of times... no indicators, no
patterns, just pure price action"), the second strategy this project has
built from a plain text description rather than an extracted document
(after SWAG). No strategy name is given in the video; named here after
how the user introduced it.

Built exactly to the video's own 3 steps:
1. **Market structure** — `engines/structure_break.py`, a new engine
   implementing the video's own "valid low/high" definition precisely
   (a low only becomes the structural invalidation reference once price,
   after making it, breaks back above the high that preceded it —
   deliberately different and more careful than this project's existing
   `market_structure.trend_state()`; see that module's docstring for the
   full reasoning, including the hand-derived test proving it does NOT
   flip on an unvalidated pullback low the way a naive break-of-support
   check would).
2. **Supply/demand zones** — `strategies/three_step_formula.py`: the
   candle immediately before an impulse move (`price_action.
   is_strong_bullish`/`is_strong_bearish`), gated to only form in the
   matching trend direction, entered on the first later touch back into
   the zone.
3. **Risk:reward filter (≥2.5:1)** — a genuinely new capability added to
   `backtest/engine.py` (`StopTargetConfig.structure_target_col` +
   `min_rr`): stop at the zone's far edge, target at the "recent
   highs/lows" the video's own worked examples use, reject any signal
   whose realized reward:risk falls short of 2.5.

## Two real bugs caught and fixed during evaluation, before any verdict

This is the most bug-prone strategy built this project, and both bugs
were caught by the same discipline used throughout: a near-zero
real-data trade count is a signal to inspect, not a result to report.

1. **"Recent highs" was initially read as `market_structure.resistance()`
   (the fractal-CONFIRMED prior swing high) instead of the running max
   high since the zone formed.** That prior swing high is, by
   construction, the very level the impulse candle just broke to form
   the zone in the first place — so it was almost always already BEHIND
   price by the time of a retest entry, making the reward leg of the RR
   calculation near-zero for the wrong reason (a stale reference, not a
   real absence of upside room). Fixed to use the running max/min since
   zone formation — the peak of the current move, matching what the
   video's own charts are visibly pointing at.
2. **The touch-detection window initially included the formation
   (impulse) bar itself**, which structurally always overlaps the zone
   it just broke away from (the zone IS the immediately preceding
   candle's range) — so signals were firing on the impulse bar, not on
   a genuine later return to the zone as the video describes. Fixed by
   excluding the formation bar from ever counting as the first touch.

Both fixes are documented in the module's own docstring/comments, not
just here. Neither loosens a rule to produce more trades — both correct
a mismatch between the code and what the video's own worked examples
actually show, caught before any PF number was trusted.

## Result after both fixes: a clean rejection, well short of even generating a workable sample

| Symbol | Timeframe | Trades (RR≥2.5) | PF | Windows profitable |
|---|---|---|---|---|
| BTC/USDT | 1h | 6 | 0.31 | 1/7 |
| ETH/USDT | 1h | 8 | 0.48 | 1/7 |
| BTC/USDT | 1d | 0 | — | 0/16 |
| ETH/USDT | 1d | 1 | 0.0 | 0/16 |

Raw signal counts before the RR filter are not tiny (118 long + 68 short
on BTC/USDT 1d alone) — steps 1 and 2 (structure + zone) fire at a
reasonable rate. Step 3 (the video's own RR≥2.5 rule) is what prunes
almost the entire set: across BTC/USDT 1d's 186 candidate signals, the
achieved reward:risk ranged from about 0.05 to 2.12 — **never once
reaching 2.5**. 1h timeframes let a handful through only because more
candidates give more chances at a favorable roll, not because the
underlying setup is stronger there.

**A diagnostic run with the RR filter removed** (not a proposed
alternative — purely to see whether the underlying zone-touch mechanism
has any edge before the filter is applied) confirms the filter isn't
unfairly discarding a good setup: BTC/USDT 1d manages PF 0.89 even with
every signal taken (60.3% win rate, but average losses outweigh average
wins), ETH/USDT 1d PF 0.72 (56.5% win rate). A decent win rate with
negative expectancy is exactly the signature of a stop that's
structurally too far from entry relative to the available reward — the
zone's far edge (stop) and the running high/low since formation (target)
just don't leave enough room on real BTC/ETH data for this specific
geometry to clear 2.5:1 with any regularity, independent of the filter.

## Overall verdict

**Does not proceed to paper trading.** Steps 1 and 2 are implemented
faithfully and produce a reasonable signal rate; step 3, applied exactly
as the video states it (2.5:1, no exceptions), reduces that to 0-8
trades per config — nowhere near enough for a PF number to mean
anything, and the diagnostic no-filter run shows the underlying
zone-touch setup has negative expectancy on real data regardless. No
sensitivity sweep was run (nothing to sweep with 0-8 trades). No
parameter was loosened to manufacture a larger sample — the two fixes
made during evaluation corrected implementation choices that didn't
match the video's own description, not the RR threshold or zone
definition itself.
