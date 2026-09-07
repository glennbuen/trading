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

## What Phase 2 does NOT include yet

Volume engine, liquidity engine (equal highs/lows, sweeps — builds on `market_structure.resistance/support`), any of the 4 strategies, signal scoring, risk manager, backtest engine, regime detection, BTC-context monitoring, journal, dashboard. See the repo README's roadmap table for the phase order.
