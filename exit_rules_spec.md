# Exit Rules Spec — Daily Timeframe Swing/Position Trades

## Purpose
Defines exit logic for positions held on daily candles. Resolves ambiguity between hard capital-protection stops and EMA-based trend-reversal signals. This spec should be treated as the single source of truth for exit logic — implement exactly as ordered below, do not infer alternate precedence.

## Core principle
Two exit systems run concurrently, but answer different questions:
- **Hard % stop** = "I was wrong about this trade" → capital preservation → ALWAYS takes priority
- **EMA(8)/EMA(4) rules** = "the trend that justified holding may be ending" → trend-health check → only evaluated on capital that has survived the hard stop

They are not equal-priority alternatives. Hard stop is a floor that overrides everything else, every day, regardless of trend read.

## Execution timing (critical — do not implement uniformly across rules)

- **Hard % stop (rule 1 below): INTRABAR, immediate.** Check continuously (every price update / every lower-timeframe candle close, e.g. 1H or 15m), not once per day. The moment price touches the stop level, exit fully — do not wait for the daily close. This is a capital-protection floor; waiting for confirmation defeats its purpose and increases realized drawdown.
- **Time stop (rule 2) and EMA rules (rules 4–5): DAILY CLOSE ONLY.** These are trend/thesis-health checks, not hard risk floors. A single intrabar wick should not trigger them — only evaluate against the completed daily candle close. This is also required for internal consistency, since EMA(8)/EMA(4) are calculated from closes.

This means the bot needs two separate check frequencies running for the same position: a continuous/high-frequency check for rule 1, and a once-per-day check (after daily candle close) for rules 2, 4, and 5.

## Evaluation order (hard stop checked continuously; rules 2–5 checked once per daily close, only if hard stop hasn't already closed the position)

1. **Hard % stop (ratcheted)** — INTRABAR
   - Initial stop: 5% or less from entry (3% acceptable if invalidation is early/high-confidence)
   - If profit reaches 4%, move stop to breakeven
   - If profit reaches 12%, move stop to lock in 6% (protects 2:1 reward:risk)
   - For tranched/scaled-in positions: stop is calculated off the **size-weighted average entry price**, not a simple average of stop levels
   - **If breached at any point (not just at daily close) → exit 100% of position immediately. Stop evaluating further rules for this trade until a new position is opened.**

2. **Time stop** — DAILY CLOSE ONLY
   - Only evaluated if hard stop did NOT trigger today
   - If position has moved sideways/against thesis for 5 days, tighten initial stop to 3%
   - If price hasn't moved per expectations after 5–8 days, exit is allowed (discretionary but bounded to this window)
   - **If triggered → exit 100%. Stop evaluating further rules.**

3. **Partial profit-take (optional, non-exit-triggering)**
   - If unrealized gain ≥ 20%, selling 20–30% of position is acceptable practice
   - This does not close the trade — remaining position continues through rules 4–5

4. **EMA(8) reversal warning** — DAILY CLOSE ONLY
   - Only evaluated if hard stop and time stop did NOT trigger today
   - If daily close falls below EMA(8) → sell 50% of remaining position
   - This is a partial de-risk, not a full exit

5. **EMA(4) x EMA(8) confirmation / failed reclaim** — DAILY CLOSE ONLY
   - Only relevant to the remaining position after rule 4 has fired
   - If price fails to close back above EMA(8) following a close below it, OR EMA(4) crosses below EMA(8) → exit remaining 100%

## Why this order matters
- Hard stop is checked first and unconditionally — it protects against being wrong, independent of what the trend indicators say.
- EMA rules 4–5 will rarely fire on losing or breakeven trades, because the hard stop will have already closed those out. In practice, EMA(8)/EMA(4) act as a "protect a winner from round-tripping" mechanism for trades that are already profitable enough to have their stop ratcheted up (post rule 1, step 2 or 3).
- This division of labor is intentional: hard stop = cut losers, EMA rules = don't give back gains on winners that are rolling over.

## ADDITION (not in original source material — flagged separately, confirm before implementing)

**Gap identified:** the original rules lock the stop at +6% once profit hits 12%, and never move it again. On strongly trending trades that run well past 12% (e.g., 30%+), this means giving back everything down to a 6% gain before any exit rule fires — the only partial protection above 12% is the +20% partial trim (rule 3) and the EMA(8) reversal signal (rule 4), neither of which is a proper trailing stop.

**Proposed fix:** above +12% profit, replace the flat +6% lock with a volatility-adjusted trailing stop:
- Use ATR-based trailing: `stop = highest_price_since_entry − (2.5 × ATR)`, recalculated each daily close, only ever moves up (never loosens)
- Alternative (Chandelier Exit style, less whipsaw-prone): same formula, but only updates when price makes a new high since entry, rather than every single close
- This stop runs alongside the EMA(8)/EMA(4) rules — it does not replace them. It replaces only the static "+6% lock" from rule 1's third tier.
- ATR period: use 14-day ATR (standard default) unless another period is already used elsewhere in the bot for consistency

**This is an addition proposed to close a real gap, not part of the original rule set.** Do not implement until explicitly confirmed — treat as optional/config-gated (`enable_atr_trailing_above_12pct: bool`) so the original flat-lock behavior remains available as a fallback.

## Known ambiguities NOT yet resolved (flag if encountered, do not guess)
- Rule 1's "3% acceptable sometimes" is a discretionary judgment call, not a deterministic condition. If building fully automated (no human override), a config flag should define when 3% vs 5% applies — otherwise default to 5% always.
- "5–8 days" for time stop is a range, not a fixed number. Default to 6 days unless told otherwise, and treat as a configurable parameter.

## Implementation note
Each of the 5 steps above should be its own discrete function, called in sequence, with each returning either `None` (no action, proceed to next check) or an exit instruction (`full_exit`, `partial_exit_50`, `partial_exit_20_30`). The first non-`None` full-exit result for a given day halts further checks for that position.

Suggested architecture: run rule 1 (hard stop) as a continuous/high-frequency monitor separate from the main daily strategy loop — e.g. a dedicated stop-loss watcher checking against live price or lower-timeframe candles. Run rules 2, 4, and 5 as part of the once-daily post-close evaluation loop. Do not merge these into a single daily-only check, or the hard stop will fail to protect against intraday moves.
