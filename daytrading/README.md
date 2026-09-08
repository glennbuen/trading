# daytrading/

A new home for genuinely intraday (same-day open-and-close) strategies,
kept separate from `cryptobot/`, which has grown into this project's
daily/weekly-swing strategy suite (TITA and everything tested alongside
it — entries and exits both driven off daily candles, positions
routinely held for days to weeks).

## Status

First build complete and evaluated: `engines/trend_filter.py` (1h+15m
both-must-agree trend filter, merged onto a 5m entry timeframe) +
`strategies/wrapper.py` (adapts each of `cryptobot/strategies/`'s
14 real-signal strategies onto this structure, reusing their entry
logic unchanged). All 14 were retested this way and **all 14
failed** — see `docs/EVALUATION_DAYTRADING_ALL.md` for the full report,
including a real cost-model bug caught and fixed along the way before
the result was trusted. Nothing in this package is ready for paper
trading.

## Relationship to `cryptobot/`

This is its own package (`daytrading/__init__.py`), not a subfolder of
`cryptobot/`, since day trading is a distinct discipline from what's
been built so far — different holding periods, different risk
management (same-day flat, not overnight/multi-day), likely different
timeframes (intraday candles rather than 1d/1w). It's expected to reuse
`cryptobot`'s existing generic infrastructure where it genuinely
applies — `cryptobot.data` (OKX market data), `cryptobot.backtest`
(the walk-forward/backtest engines), `cryptobot.risk` (position sizing,
risk limits) — rather than duplicating any of that. What's day-trading-
specific (engines, strategies, evaluation scripts) belongs here.

## What goes here, once there's something to build

Following this project's established practice for every strategy so
far: built from an explicit source the user provides (a named trader's
system, a video transcript, a book excerpt) or a clearly-scoped request
— not invented from scratch — then tested with the same rigor as
everything in `cryptobot/`: no-lookahead-safe engines, real OKX walk-
forward evaluation, honest reporting including negative results, no
parameter tuning in response to a disappointing outcome.
