# Architecture

## Package layout

```
cryptobot/
├── data/
│   ├── exchange.py       # ExchangeProvider — the ONLY module that talks to ccxt/an exchange
│   └── market_data.py    # MarketDataProvider — canonical OHLCV schema, consumed by everything else
└── engines/
    ├── price_action.py    # candle-shape primitives (Phase 2)
    └── market_structure.py  # swing points, trend state, BOS, S/R (Phase 2)
tests/                     # one test file per module, from day one
```

Strategies and engines never call `ccxt` or `ExchangeProvider` directly — they consume `MarketDataProvider`, which returns a fixed schema (`ts, dt, open, high, low, close, volume`). This is what makes an exchange swap or a second data source later a one-file change instead of a repo-wide one.

The 7 standalone `okx_*.py` bots at the repo root predate this package and are kept as-is — completed, documented research (see `README.md`), not superseded code. They are not built on this package and won't be retrofitted onto it; new strategy work happens here instead.

## How look-ahead bias is prevented (§22)

This is the single most load-bearing property of the whole system, so it's documented explicitly rather than left implicit in the code.

**The general technique, used everywhere a value could leak from the future:** compute the value, then delay its availability by exactly the number of bars it actually takes to know it, using pandas `.shift()` — never a negative shift, never `.rolling()` on an un-shifted series when the current bar would inflate its own baseline. This was first proven in this repo in the standalone bots' multi-timeframe filters (`available_at = ts + timeframe_ms` + `merge_asof(direction="backward")`) and is now formalized here.

**Where it applies in Phase 2, concretely:**

1. **`price_action.relative_candle_size` / `is_strong_bullish` / `is_strong_bearish`** — a candle's "size" is judged against the average of the *preceding* N bars (`.shift(1).rolling(N)`), not including itself. Including itself would let an unusually large candle inflate its own baseline and always look "average."

2. **`price_action.breakout_level_up/down`** — the level being broken is the max/min of the *preceding* N bars (`.shift(1).rolling(N)`), so a breakout candle is judged against a level that existed before it printed, not one contaminated by its own high/low.

3. **`price_action.is_failed_breakout_*`** — uses `_bars_since()` and `.ffill()` of a past breakout's level. `ffill` only ever propagates a value forward in time from a row that already happened; it cannot pull in anything from a later row. Safe by construction.

4. **`market_structure` swing detection — the subtle one.** A swing high at bar `i` is a fractal: by definition it requires `right` bars *after* `i` to confirm nothing higher followed. That means it is genuinely not knowable until bar `i + right`. Two series are exposed for every swing:
   - `swing_high_raw` / `swing_low_raw` — the retrospective pattern (uses future bars internally; for research/plotting only, never for live signals or backtest entries).
   - `swing_high_confirmed` / `swing_low_confirmed` = `raw.shift(right)` — True at bar `i + right`, the first bar where it's actually knowable. **Every other function in the module (`resistance`, `support`, `higher_high`, `trend_state`, `break_of_structure_*`) is built only from the confirmed series.** Nothing downstream can accidentally consume the un-shifted version.

5. **`market_structure.break_of_structure_up/down`** — compares the *current* close against the resistance/support level as it stood on the *prior* bar (`resistance(df).shift(1)`), so the level a breakout is tested against can't itself be updated by the same bar's own high.

6. **`market_structure.previous_day_levels`** — only a fully-closed prior UTC day's high/low is used (`.shift(1)` on the daily-resampled table), the same pattern validated in `okx_vwap_pivot_bot.py`'s pivot calculation.

**How this is verified, not just asserted:** every engine module has a `TestNoLookahead` test class using **truncation invariance** — compute every output column on the full dataset, then again on a truncated prefix (`df.iloc[:k]`), and assert the two are identical on every overlapping row. If a function were secretly using data beyond row `k`, truncating at `k` would change its answer at rows `< k`, and the test would fail. This isn't a style check; it's a direct, mechanical test of the property the whole codebase depends on. All current instances pass (`tests/test_price_action.py`, `tests/test_market_structure.py`).

## Testing

`pytest tests/` — 33 tests as of Phase 2, covering: candle-shape correctness on hand-built synthetic candles, swing/trend classification on a hand-built zigzag series with known anchor points, the OHLCV backward-pagination logic against a fake exchange (including a regression test for the forward-pagination bug found and fixed earlier in this project — see `okx_*.py` commit history), and the truncation-invariance no-lookahead checks above. No test hits the network; the exchange tests use `FakeCcxtExchange`, a controllable in-memory stand-in.

## Phase 3 — volume + liquidity engines

`engines/volume.py` and `engines/liquidity.py` followed the same rules above. One finding worth recording: the first version of `liquidity.swept_and_reclaimed_above/below` checked only "was price below the level within the last N bars" — but since a bar's low is always ≤ its close, a price sitting below a level for several consecutive bars re-satisfies that check every bar, making the recency window meaningless. Fixed by requiring the dip to be **fresh** (the prior bar's close was still at/above the level) — caught by `tests/test_liquidity.py`, not by inspection.

`bars_since()` was extracted to `cryptobot/utils.py` when `liquidity.py` needed the exact logic already private to `price_action.py` — fixed before the duplication recurred, per the Phase 1 audit's finding about the original 7 bots.

## Phase 4 — first strategy: `strategies/breakout_retest.py`

Unlike the engines (one row → one deterministic value), Breakout+Retest spans a variable number of bars between the breakout and its confirmation. It's implemented as a single vectorized pass using `groupby(episode_id).cummax()/.cumsum()` rather than a bar-by-bar Python loop:

- `episode_id = breakout_event.cumsum()` — increments every time a new qualifying breakout occurs, partitioning the timeline into episodes.
- `retested_in_episode = retest_touch.groupby(episode_id).cummax()` — True from the first valid retest onward, resets to False at the next episode. `cummax` on a boolean is "any so far," and like every other technique here it only ever looks backward within the group.
- `is_first_in_episode = confirmation_raw.groupby(episode_id).cumsum() == 1` — ensures entry fires exactly once per setup, not on every subsequent new high.

A rejection candle at the retest (`price_action.is_bullish_rejection`/`is_bearish_rejection`) is recorded as extra context but deliberately **not required** to fire entry — the lesson from the 7 standalone bots earlier in this project (`okx_ema_rsi_bot.py` especially) is that stacking too many simultaneous required conditions onto an already multi-stage pattern makes it vanishingly rare. Smoke-tested against real OKX data: 19-20 long signals over ~2.5 months of 1h BTC/ETH, 11 over 5+ years of daily BTC — a sane frequency, not the 0-2-signals-in-years problem or the 60+-trades-a-month fee-bleed problem seen previously.

## Phase 5 — risk manager + backtest engine + walk-forward

`engines/volatility.py` was added first (ATR/true-range) — needed for stop-loss sizing (§18) and not scoped into any earlier engine.

`risk/risk_manager.py` centralizes what was previously duplicated per-bot across all 7 standalone scripts: position sizing, daily/weekly loss limits, max consecutive losses, cooldown, max open positions/exposure, emergency shutdown. One deliberate improvement over the earlier bots: day/week boundaries are computed from actual UTC calendar timestamps (`dt.date()`, ISO week), not the `bars_per_day = 24 / tf_hours` heuristic those bots used — the heuristic silently misbehaves whenever a timeframe doesn't evenly divide a day; timestamp boundaries don't have that failure mode and work identically in backtest and live.

`backtest/engine.py` is event-driven, bar-by-bar. Two execution-realism decisions worth recording:

1. **Next-bar-open fills.** A signal computed from bar `i`'s close (only knowable once bar `i` has fully closed) executes at bar `i+1`'s open, not bar `i`'s own close. The 7 earlier standalone bots all used same-bar-close fills as a simplification; this is a deliberate rigor upgrade for this engine. Verified directly by `tests/test_backtest_engine.py::TestNextBarOpenFill`, which engineers a large gap between the signal bar's close and the next bar's open and asserts the fill price reflects the latter.

2. **End-of-data handling — a real bug found by testing, not just a simplification avoided.** The first version only ever appended a completed `Trade` on exit, so a position opened near the end of a dataset that never hit its stop/target within the remaining bars simply vanished from the results: not counted in `num_trades`, not reflected in `final_equity`. A test asserting a specific fixture would produce exactly one trade caught this (`0 == 1`, not the value mismatch I was originally checking for). Fixed by force-closing any still-open position at the last available bar's close, honestly labeled `exit_reason="end_of_data"` rather than a real stop/target fill.

Stop-loss supports `"atr"` and `"structure"` methods (a caller-supplied per-bar level column, e.g. a strategy's broken level, with an ATR floor as a safety minimum — the same "wider of structural distance vs ATR floor" pattern used throughout the 7 earlier bots). Take-profit is fixed-R-multiple only for now; the spec lists five TP approaches and says to backtest each, and building all five before any has been evaluated once would repeat the over-building this project has avoided everywhere else.

**Known limitation, stated rather than silently left:** the engine tracks at most one open position at a time, matching every one of the 7 earlier bots. `RiskLimits.max_open_positions` defaults to 1 to match; true concurrent multi-position tracking would need a list-based position tracker and is deferred.

`backtest/walk_forward.py` splits a date range into rolling windows and backtests each independently. One design choice worth noting: `signal_fn` runs on the FULL dataset exactly once, and windows are then sliced from that result — not re-run per window. Re-running per window would reset every engine's warmup at each boundary (e.g. market_structure needs real prior history before a confirmed swing means anything), understating how much history a live system would actually have accumulated by that point. This doesn't reintroduce lookahead: each engine's own no-lookahead guarantee already ensures a value at bar `i` depends only on bars `<= i`, regardless of where a later window boundary falls.

**Mechanical smoke test only (not Phase 6's evaluation):** ran Breakout+Retest through `run_walk_forward` on 3000 real 1h BTC/USDT candles, 4 rolling 30-day windows. The pipeline ran end-to-end with no errors and produced non-degenerate metrics — including a real split (1 profitable window, 3 unprofitable) that previews exactly the kind of walk-forward inconsistency check Phase 6 exists to formalize properly (across symbols, with a real verdict). No conclusion about the strategy is drawn here.

## Phase 6 — first real verdict: Breakout+Retest evaluated, and rejected

`scripts/evaluate_strategy.py` — a reusable walk-forward evaluation harness (generic over any strategy's `signal_fn` + column names, so it's ready for Phase 11's strategy comparison too) — ran Breakout+Retest across BTC/USDT and ETH/USDT, at 1h (8000 real candles, ~11 months) and 1d (3000 real candles, 8.2 years spanning multiple bull/bear/chop regimes), with every parameter left at its default. Full report: `docs/EVALUATION_BREAKOUT_RETEST.md`.

**Verdict: insufficient evidence of a reliable edge.** Profit factor 0.68-1.01 across all four configs (none clearing the 1.2 bar this project has held every strategy to), profitable in a minority of walk-forward windows everywhere, no parameter tuned in response. Per spec §41 this is treated as a legitimate, useful result — not a failure needing a re-run with different numbers.

The evaluation itself surfaced two real findings, independent of the profitability verdict:

1. **A genuine risk-manager gap — found AND fixed.** One run hit an 11-consecutive-loss streak despite `max_consecutive_losses=3` being configured. Root cause: `RiskManager` reset its loss counter the instant it triggered a halt, but the halt only blocks a signal that lands *inside* the 24h halt window — on sparse 1h signals, the next attempt often arrived after the halt had already expired, so the breaker "fired" without actually preventing anything, cycle after cycle. **Fixed**: the counter no longer resets on trigger, only on an actual win — so a persistent losing streak keeps re-arming the halt instead of "looking safe" again after exactly 3 losses. Verified by re-running the exact window that surfaced it (halt rejections 1→3, worst streak 11→10) plus two new regression tests. The fix changed risk control, not the profitability verdict — as it should.
2. **A metric-methodology limitation in the evaluation harness itself.** Walk-forward windows reset to the same starting equity independently, so "worst window drawdown" is not the same as one continuous multi-year equity curve's peak-to-trough drawdown. The report states this caveat explicitly rather than presenting the smaller per-window number as the full risk picture. Not fixed yet.

**Both gaps subsequently closed** (see `docs/EVALUATION_BREAKOUT_RETEST.md` for full detail):
- `chain_equity_curves()` / `chained_max_drawdown_pct()` added to `backtest/walk_forward.py` — converts each window's equity curve to per-bar returns and compounds them onto one continuous curve, so window boundaries no longer hide a drawdown spanning across them. Verified with a hand-computed synthetic test before trusting it on real data; the real BTC/ETH 1h/1d results show the true cumulative drawdown is roughly **2x** the single-window figure in every config.
- `scripts/parameter_sensitivity.py` — perturbs `atr_mult_stop`, `target_r_multiple`, `volume_threshold`, `retest_window` at ±10/±20% one at a time on BTC/USDT 1h. No cliff/collapse in any of the four; the rejected verdict holds across the whole tested neighborhood, not just at the exact default values. `volume_threshold` shows the one real (if modest) trend — tighter filters perform somewhat better, though even the best value tested doesn't clear PF 1.2. The suspiciously flat `retest_window` result was verified directly (raw signal counts barely move across 8-50) rather than assumed to be a script bug.

## Phase 7 — signal scoring (spec §14-15)

`cryptobot/scoring.py`: a configurable, weighted, explainable score over five components (market structure, price action, volume, liquidity, risk/reward), default weights matching the spec's own worked example (25/25/20/15/15 = 100). Deliberately decoupled from any one strategy: `SignalInputs` is a small explicit set of already-extracted values, not a DataFrame — the CALLER maps a specific strategy's own column names onto it (see `scripts/demo_signal_scoring.py` for Breakout+Retest's mapping), so the scorer stays reusable as the remaining 3 strategies get built with different engine combinations. `SignalScore.explain()` formats output to match spec §14's illustration exactly.

This does **not** change how Breakout+Retest decides to enter a trade — that logic (Phase 4) is untouched, and its rejection (Phase 6) stands. Scoring is demonstrated against the strategy's real historical signals purely for illustration and journaling (§31's "every trade must explain its score"), not as a fix.

**Demonstrated on 153 real historical signals** (BTC/USDT 1h, 8000 candles): scores ranged 26.5-95.5/100, mean 61, only 25.5% cleared the spec's own illustrative 70/100 threshold — real, meaningful variation across signals, not a degenerate always-high or always-low result.

**One honest finding, not glossed over:** every single signal's risk_reward component came out identical (R=2.0 for all 153) — because Breakout+Retest uses a *fixed* `target_r_multiple`, not a variable structure-based target, so that component carries zero discriminating information for this particular strategy. This is a property of the strategy's exit design, not a scoring-system bug — a strategy with a variable target (a likely design for the remaining 3 strategies, e.g. "previous swing" per spec §19) would show real variation here.

A natural follow-up question this raises — does filtering to score≥70 actually improve the strategy's profit factor? — was **not tested**; that would require re-running the full walk-forward evaluation with the score as an additional gate, which is a new analysis, not part of building the scoring infrastructure itself. Flagged, not answered.

## Strategy 2 of 4 — Breakout (Strategy A), built as a control comparison

`cryptobot/strategies/breakout.py`: same structural-break + volume-confirmation core as Breakout+Retest, but enters ON the breakout with no wait for a retest, plus an explicit consolidation-before-breakout filter (spec §10's "reject weak breakouts", made concrete via a rolling ATR percentile-rank check rather than left vague). Built specifically to answer: does Breakout+Retest's retest requirement actually help, or was it just filtering trades either way?

One real bug found and fixed via testing before real-data evaluation: the initial percentile-rank formula used `<=` when checking where the current bar's ATR ranks in its trailing window, which on a perfectly flat/tied window counts every value as "at or below" the current one — ranking a completely quiet market at the *top* of its own range instead of the bottom, backwards from what "consolidating" should mean. Fixed with strict `<`, matching the convention already used in this project's earlier standalone bots' adaptive-ATR logic.

**Evaluated the same way as Breakout+Retest** (full report: `docs/EVALUATION_BREAKOUT.md`): worse on 3 of 4 configs (PF 0.51-0.61 vs Breakout+Retest's 0.68-0.88), confirming the retest requirement does real work, not just arbitrary filtering. One config (BTC/USDT 1d) crossed PF 1.2 for the first time in this entire project — but on inspection, driven partly by 100%-win-rate windows with only 1-3 trades each, and the same strategy/parameters on ETH/USDT 1d scored a poor 0.61, the exact "works on one symbol only" pattern this project has flagged as a red flag every time it's appeared. Treated as a lead worth a larger sample and a sensitivity sweep, not a result. **No parameter tuned in response.**

## Strategy 3 of 4 — Trend Pullback

`cryptobot/strategies/trend_pullback.py`: established trend (market_structure.trend_state) → strong impulse candle anchoring an episode → controlled pullback that must not violate the confirmed swing level from just before the impulse → at least one genuine low-volume pullback bar (Wyckoff/Darvas "effort vs result", made concrete rather than left as a comment) → continuation beyond the episode's prior extreme with volume expansion again. Same episode-scan technique as Breakout+Retest (`groupby(episode_id).cummax()/.cumsum()`).

Two test-fixture bugs found and fixed while building the synthetic test scenario (neither a production bug, both caught by explicit sanity assertions before being mistaken for one): a hand-derived 4-anchor "downtrend" zigzag never actually reached a confirmed `trend_state == "down"` (fixed by reusing the already-proven 8-anchor zigzag from `test_market_structure.py`), and a perfectly-flat zigzag base gave a zero relative-candle-size baseline, silently making `is_strong_bullish/bearish` permanently `False` on whatever candle came next.

One real strategy-design **interaction** worth recording (documented in the module, not a bug): if a "continuation" candle happens to itself qualify as a fresh strong-candle impulse, it starts a *new* episode via `episode_id = impulse_event.cumsum()` incrementing on that same bar, rather than confirming the old one. Defensible (a big new impulse arguably is a fresh setup) but non-obvious — the same mechanism Breakout+Retest's `breakout_event` uses to legitimately retrigger on an independent subsequent breakout.

**Evaluated the same way as the other two** (full report: `docs/EVALUATION_TREND_PULLBACK.md`): worse than both prior strategies on BTC/USDT 1h (PF 0.35, the worst 1h result of the three strategies tested). One config (ETH/USDT 1d) crossed PF 1.2 — on weaker evidence than Breakout Strategy A's exception: 4 of 6 "profitable" windows are 100%-win-rate on 1-2 trades. **A cross-strategy pattern worth naming**: each strategy's one PF>1.2 exception has been on a *different* symbol (Strategy A: BTC/USDT 1d; Strategy C: ETH/USDT 1d) — that inconsistency in which symbol "wins" is itself evidence of noise scattering around a real non-edge, not signal. No parameter tuned in response.

## Strategy 4 of 4 — Liquidity Sweep Reversal, and Phase 11's comparison

`cryptobot/strategies/liquidity_sweep_reversal.py`: important prior level (structural support/resistance) → sweep-and-reclaim (reusing `liquidity.swept_and_reclaimed_above/below` as-is, including its own "freshness" fix from Phase 3) → market-structure shift (prior trend must NOT already be in the reclaim's direction — a genuine reversal setup, distinct from Strategy C's dip-buy-within-an-uptrend) → volume confirmation. Single-bar signal, no episode tracking needed — the sweep geometry already spans its own bars internally via `max_bars_to_reclaim`.

**By far the highest-frequency of the four strategies** (448 raw 1h signals vs. 57-122 for the others) — and it shows directly in the results: **0/7 and 1/7 profitable windows on 1h** (the worst of any config across all four strategies), chained drawdown **22-25%** (more than double the worst seen elsewhere), and the heaviest fee load. A direct real-data recurrence of the fee-bleed-from-overtrading pattern first identified in this project's standalone `okx_scalper_bot.py`/`okx_bollinger_bot.py`. ETH/USDT 1d again crosses PF 1.2 (1.21) — but this exception is meaningfully more credible than the prior three (52 trades, only one small-sample artifact window, a real spread of multi-trade window outcomes) — still not validated (fails on BTC/USDT 1d, same timeframe: 0.62), but worth distinguishing from the flimsier exceptions in Strategies A and C rather than dismissing identically. Full report: `docs/EVALUATION_LIQUIDITY_SWEEP_REVERSAL.md`.

**All 4 spec strategies now built, tested, and evaluated with identical rigor — `docs/STRATEGY_COMPARISON.md` (spec §24/Phase 11) consolidates them.** Breakout+Retest comes out most defensible on every axis (expectancy, drawdown, consistency, OOS-window survival rate) — not because it works, but because it's the least fragile of four unvalidated strategies. Each of the other three shows exactly one PF>1.2 exception, never on the same symbol twice across strategies and never confirmed on both BTC and ETH simultaneously — named explicitly as evidence of noise scattering around a real non-edge, not a hidden signal. Per spec §24's own instruction ("do not simply select the strategy with the highest historical return"): **none of the four should proceed to paper trading as currently configured.**

## Strategy 5 — Ichimoku Cross (outside the original 4, requested directly)

`cryptobot/engines/ichimoku.py` + `cryptobot/strategies/ichimoku_cross.py`: the classic full-system Ichimoku signal (TK cross + price-vs-cloud + projected-cloud-color + Chikou confirmation), a genuinely different hypothesis from the 4 spec strategies (which all compose the same four engines). Kijun-sen used as the structural stop — a first for this project (every prior strategy used ATR-only/ATR-floored stops).

The engine module is deliberately explicit about Ichimoku's classic lookahead trap: Senkou spans are conventionally *plotted* 26 bars ahead of where they're computed. The cloud actually surrounding TODAY's price was computed 26 bars ago (`cloud_top`/`cloud_bottom` = `.shift(displacement)` of the raw span formulas) — using the raw, un-shifted spans as "today's cloud" would be a real bug, not a style choice.

**A real bug was found and fixed via testing** (not the cloud-shift logic, which was correct from the start — a different, more mundane issue): `~` (bitwise inversion) on an object-dtype boolean Series doesn't perform logical negation (`~True` returns `-2`, not `False`). This made `tk_cross_up` fire on every bar after a crossover instead of exactly once, at it — caught by a test asserting the exact fire count against a fixture with a known, single, real crossover. Fixed with the same `.astype(bool)` guard `market_structure.py` already used for the same reason; verified via `grep` that this risky pattern didn't exist anywhere else in the package, so none of the 4 already-evaluated spec strategies were affected.

**Evaluated the same way as every prior strategy** (full report: `docs/EVALUATION_ICHIMOKU.md`): the most substantive result seen across all 5 strategies tested this session — ETH/USDT 1d hit PF 1.49 (the highest of any config, highest win rate too), with real multi-trade winning windows, not just small-sample artifacts, and BTC/USDT 1d closed to 0.84, the narrowest BTC/ETH gap any strategy has shown. Still not validated: BTC/USDT 1d remains below 1.0, three separate multi-trade windows show PF exactly 0.0, a full 6-month stretch (H2 2021) produced zero signals at all, and no parameter sensitivity has been run. Worth a closer look if this project continues — the closest thing to a lead this entire session has produced — but "worth a closer look" and "validated" are not the same statement. No parameter tuned in response. Do not proceed to paper trading.

## What's not built yet

Regime detection, BTC-context monitoring, the full trade journal (beyond the backtest engine's own `rejected_signals` list — already a real instance of spec §31's "record rejected signals too"), dashboard, paper trading, and live exchange integration for the cryptobot package. See the repo README's roadmap table for phase order.
