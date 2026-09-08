# Strategy Evaluation — Triple Screen (Alexander Elder)

Source: the well-documented, widely-taught standard version of Dr.
Alexander Elder's Triple Screen Trading System ("Trading for a Living",
1993) — no specific transcript or document was provided for this one
(confirmed with the user before building, a departure from every other
strategy this project has tested, all of which were built from a
verbatim source). Built as described in that book's standard treatment,
not from a fabricated or guessed variant.

Three screens, exactly as Elder describes them:
1. **Screen 1 (weekly tide)**: the WEEKLY MACD-Histogram's slope —
   rising = bullish tide (longs only), falling = bearish tide (shorts
   only). Direction filter only, never itself a trigger. Required a new,
   genuinely reusable engine (`engines/multi_timeframe.py`,
   generalizing the weekly-merge pattern first built for
   `parabolic_risk.py`) to merge the weekly read onto daily bars without
   lookahead.
2. **Screen 2 (daily wave)**: Force Index(2) (`engines/force_index.py`,
   new — Elder's own indicator) dipping against the tide identifies a
   pullback. Armed for a short window (3 bars) waiting for Screen 3,
   matching Elder's own "leave the order in for a day or two."
3. **Screen 3 (entry trigger)**: close breaks the 2-day high/low —
   adapted from Elder's actual resting buy-stop order to this project's
   close-based, next-bar-fill convention (reusing already-tested
   `price_action.py` primitives, no new engine needed here).

Exit: structural stop at the far side of the Screen-3 breakout window
plus the usual ATR floor, fixed 2R target — Elder's own text discusses
several trailing-stop approaches without one crisp numeric rule, the
same kind of gap this project has handled for every prior book/deck
source without an unambiguous exit.

## Result

| Symbol | Trades | PF | Win% | Windows profitable | Chained DD% |
|---|---|---|---|---|---|
| BTC/USDT | 107 | 1.02 | 36.45 | 7/16 | 7.80 |
| ETH/USDT | 101 | 1.15 | 39.60 | 9/16 | 4.68 |

**A genuinely well-sampled result, not a thin-sample dismissal.** Every
one of 16 windows on both symbols has 4-11 trades — never the 1-2-trade
`PF=inf` artifact pattern that has undermined most "promising" numbers
elsewhere in this project. Real variation across regimes on both
symbols (several clearly negative windows alongside several clearly
positive ones, e.g. BTC's 2020-12-09 window at PF 7.04 vs its
2022-06-02 window at PF 0.0). This is closer in character to
Breakout+Retest's profile (evenly mediocre, well-distributed, not
artifact-driven) than to any of the thin-sample cases.

**Neither symbol clears the 1.2 threshold this project has used
throughout as the bar for further scrutiny.** BTC sits at breakeven
(1.02), ETH is closer but still short (1.15). Per this project's own
established precedent (e.g. MFI Reversal's ETH 1.08 config, `docs/
EVALUATION_MFI_REVERSAL.md`: "doesn't even clear the 1.2 threshold...
so there was no promising number here to interrogate further with a
parameter-sensitivity sweep"), no sensitivity sweep was run here either.

## Overall verdict

**Does not proceed to paper trading.** A faithful implementation of a
well-known, credible strategy, evaluated with a genuinely good trade
sample on real BTC/ETH data, lands right around breakeven on both
symbols — not a small-sample fluke, not a fee-bleed collapse, just no
edge clearing this project's bar. No parameter was tuned in response.
This adaptation's exit (structural stop + fixed 2R) and Screen 2's
timing window (3 bars) are both flagged as operational choices Elder's
own text leaves open — a different, equally defensible choice on either
could move the number, but per this project's standing rule, that isn't
grounds to go looking for one that does.
