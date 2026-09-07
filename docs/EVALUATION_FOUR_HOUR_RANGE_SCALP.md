# Strategy Evaluation — "4-Hour Range" Scalp (YouTube video)

Source: the user's own transcript of a YouTube scalping video ("a
simple yet effective scalping strategy that works every single day...
no indicators or long preparations... completely rule-based"), the
third strategy this project has built from a plain text description
(after SWAG and the 3-Step Formula). Only crypto (BTC/USDT, ETH/USDT via
OKX) is tested — the video also demonstrates forex and gold, which
aren't available through this project's OKX data pipeline; every other
strategy in this project has likewise only ever been evaluated on the
symbols the data pipeline actually covers.

Built exactly to the video's own 3-step checklist:
1. **The range** — `engines/session_range.py` (new): the high/low of
   the first 4 hours of each NY-timezone calendar day, usable from the
   moment that window closes through the rest of that NY day. Built
   carefully with real timezone conversion (`America/New_York`, not a
   fixed UTC offset) since the video explicitly and repeatedly stresses
   this must be NY local time, not the exchange's raw UTC-aligned 4h
   candle boundaries.
2. **The setup** — a 5-minute candle must fully CLOSE outside the range
   (a wick alone doesn't count, verified by a hand-built test matching
   the video's own worked example), then a later candle closes back
   inside, same NY day. Multiple independent setups per day are all
   valid, matching the video's own statement.
3. **The entry** — breakout-up-then-reentry -> short; breakout-down-
   then-reentry -> long (fading the failed breakout). Stop = the exact
   high/low of the breakout excursion (tracked via the same episode-scan
   technique used throughout this project). Take-profit = 2x the stop
   distance — the video's own explicit rule, and already this project's
   existing default, so no new backtest-engine capability was needed
   here (unlike `three_step_formula.py`).

One explicit thing NOT implemented: the video's own discretionary
exception ("if the breakout was too large, I used the nearest key level
instead of the exact high/low for the stop") — this is acknowledged in
the video itself as a subjective, per-chart judgment call with no stated
numeric trigger, so it's flagged in the module docstring rather than
implemented as a rule. The literal excursion extreme is always used.

## Result: a clean, well-sampled rejection

| Symbol | Trades | PF | Win% | Windows profitable | Chained DD% |
|---|---|---|---|---|---|
| BTC/USDT | 138 | 0.43 | 31.88 | 1/12 | 16.05 |
| ETH/USDT | 129 | 0.40 | 28.68 | 2/12 | 18.31 |

5m data, 14-day walk-forward windows, ~6 months of real OKX history
(2026-03-17 to 2026-09-07 — the longest 5m history reasonably fetchable
in one run).

**This is one of the more credible rejections in this project, not a
thin-sample dismissal.** Every one of the 12 walk-forward windows on
both symbols has 5-19 trades — never the 1-2-trade artifact pattern that
undermined several other "promising" strategies elsewhere in this
project (there's no promising number here to begin with, but the sample
quality is worth naming: this isn't a case of "not enough data to
tell"). Win rates (28.68-31.88%) are nowhere near the video's own
reported figures (72% crypto, 83% forex, 60% gold, admittedly on tiny
7-10 trade samples the video itself flagged as too small to trust) —
with a fixed 2R target, this strategy needs roughly a 33%+ win rate just
to break even before fees, and both symbols sit at or below that
threshold before fees are even applied.

No sensitivity sweep was run — there is no promising config anywhere in
this result to interrogate further; both symbols fail uniformly across
essentially every window.

## A plausible reason, stated as a hypothesis not a fix

This strategy is a fade of a failed breakout (price closes outside the
range, then reverses back in — the entry bets on continued mean
reversion back toward and through the opposite side of the range).
Crypto's intraday microstructure on BTC/ETH is comparatively
momentum-heavy relative to the video's own examples — a confirmed close
outside a well-defined range is not infrequently the START of a real
move, not a false breakout, especially on majors with deep liquidity and
persistent trend-following flow. This is offered as a plausible
explanation for the pattern seen, not a basis for adjusting the
strategy — no rule was loosened or parameter tuned in response to this
result.

## Overall verdict

**Does not proceed to paper trading.** A faithful, no-lookahead-safe
implementation of all 3 steps, evaluated on real data with a large and
consistently-distributed trade sample across both symbols, shows a
clear negative edge (PF 0.40-0.43) — the opposite of the video's own
claimed results, which were themselves based on samples (7-10 trades)
the video's own narration acknowledged were too small to draw firm
conclusions from. No parameter was tuned or rule loosened in response.
