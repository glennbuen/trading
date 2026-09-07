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

## What's not built yet

Signal scoring, risk manager, backtest engine (with walk-forward), regime detection, BTC-context monitoring, journal, dashboard, and the remaining 3 strategies (plain breakout, trend pullback, liquidity sweep reversal). See the repo README's roadmap table for the phase order. Breakout+Retest has NOT been backtested yet — the signal counts above are frequency sanity checks only, not a performance claim.
